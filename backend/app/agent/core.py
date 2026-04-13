"""
Agent 核心逻辑 - LangGraph 状态图版本
支持云端（DashScope）和本地（Ollama）模型
"""
import json
import queue as _queue
import threading
import time
import uuid
from typing import Any, Generator, TypedDict

from langgraph.graph import END, StateGraph
from openai import OpenAI
from langsmith import traceable
from langsmith.wrappers import wrap_openai

from app.config import (
    CLOUD_API_KEY, CLOUD_BASE_URL,
    LOCAL_API_KEY, LOCAL_BASE_URL, LOCAL_MODEL_IDS,
    DEFAULT_MODEL,
)
from app.agent.prompts import SYSTEM_PROMPT
from app.tools import TOOLS_SCHEMA, TOOL_FUNCTIONS
from app.long_memory import get_memories

# ── 两个 OpenAI client，按模型类型选用 ──────────────────
_cloud_client = wrap_openai(OpenAI(api_key=CLOUD_API_KEY or "placeholder", base_url=CLOUD_BASE_URL))
_local_client = wrap_openai(OpenAI(api_key=LOCAL_API_KEY, base_url=LOCAL_BASE_URL))


def _get_client(model: str) -> OpenAI:
    return _local_client if model in LOCAL_MODEL_IDS else _cloud_client


TOOL_LABELS = {
    "search_web":       "正在搜索网页",
    "search_knowledge": "正在查询知识库",
    "read_file":        "正在读取文件",
    "write_file":       "正在写入文件",
    "run_python_code":  "正在执行代码",
    "query_database":   "正在查询数据库",
}

MAX_ROUNDS = 15
MAX_TOOL_RESULT = 2000
MAX_TOOL_ROUNDS_KEPT = 6


@traceable(run_type="tool")
def _run_tool(name: str, args: dict) -> str:
    func = TOOL_FUNCTIONS.get(name)
    if func is None:
        return f"未知工具: {name}"
    try:
        return str(func(**args))
    except Exception as e:
        return f"工具执行出错: {e}"


def _trim_tool_result(text: str) -> str:
    if len(text) <= MAX_TOOL_RESULT:
        return text
    return text[:MAX_TOOL_RESULT] + f"\n…（已截断，原始长度 {len(text)} 字符）"


def _sliding_window(messages: list[dict]) -> list[dict]:
    tool_rounds = [i for i, m in enumerate(messages)
                   if m.get("role") == "assistant" and m.get("tool_calls")]
    if len(tool_rounds) <= MAX_TOOL_ROUNDS_KEPT:
        return messages
    oldest = tool_rounds[0]
    end = oldest + 1
    while end < len(messages) and messages[end].get("role") == "tool":
        end += 1
    return messages[:oldest] + messages[end:]


# ════════════════════════════════════════════════════════
#  LangGraph 状态图
# ════════════════════════════════════════════════════════

class AgentState(TypedDict):
    """
    在图的所有节点之间流转的状态。
    messages: 完整对话历史（含 system prompt）
    model:    使用的模型 ID
    rounds:   已执行的 LLM 调用轮次
    _queue:   流式输出队列（不做持久化，仅运行时使用）
    """
    messages: list[dict]
    model: str
    rounds: int
    _queue: Any  # queue.Queue，节点向此队列 put (type, text) 元组


# ── 节点 1：调用 LLM ────────────────────────────────────
def _node_call_model(state: AgentState) -> dict:
    """
    流式调用 LLM，收集 content 和 tool_calls。
    文字 chunk 实时推入队列，工具调用参数在本节点累积。
    """
    client = _get_client(state["model"])
    q: _queue.Queue = state["_queue"]
    messages = state["messages"]

    # 流式请求（兼容不支持 stream_options 的 Ollama）
    try:
        stream = client.chat.completions.create(
            model=state["model"],
            messages=messages,
            tools=TOOLS_SCHEMA,
            stream=True,
            stream_options={"include_usage": True},
        )
    except Exception:
        stream = client.chat.completions.create(
            model=state["model"],
            messages=messages,
            tools=TOOLS_SCHEMA,
            stream=True,
        )

    content_parts: list[str] = []
    tool_calls_map: dict[int, dict] = {}  # index → {id, name, arguments}

    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta

        # 文字内容 → 实时推到队列（前端实时显示）
        if delta.content:
            content_parts.append(delta.content)
            q.put(("chunk", delta.content))

        # 工具调用参数 → 流式累积（参数可能分多个 chunk 到达）
        if delta.tool_calls:
            for tc in delta.tool_calls:
                idx = tc.index
                if idx not in tool_calls_map:
                    tool_calls_map[idx] = {"id": "", "name": "", "arguments": ""}
                if tc.id:
                    tool_calls_map[idx]["id"] = tc.id
                if tc.function:
                    if tc.function.name:
                        tool_calls_map[idx]["name"] += tc.function.name
                    if tc.function.arguments:
                        tool_calls_map[idx]["arguments"] += tc.function.arguments

    # 补全空 tool_call_id（Ollama 兼容）
    for info in tool_calls_map.values():
        if not info["id"]:
            info["id"] = f"call_{uuid.uuid4().hex[:8]}"

    # 构建 assistant 消息
    assistant_msg: dict = {
        "role": "assistant",
        "content": "".join(content_parts) or None,
    }
    if tool_calls_map:
        assistant_msg["tool_calls"] = [
            {
                "id": info["id"],
                "type": "function",
                "function": {"name": info["name"], "arguments": info["arguments"]},
            }
            for info in tool_calls_map.values()
        ]

    new_messages = _sliding_window(messages + [assistant_msg])
    return {
        "messages": new_messages,
        "rounds": state["rounds"] + 1,
    }


# ── 节点 2：执行工具 ────────────────────────────────────
def _node_run_tools(state: AgentState) -> dict:
    """
    读取最新 assistant 消息中的 tool_calls，逐一执行。
    执行前把状态 label 推入队列（前端显示"正在搜索..."）。
    """
    q: _queue.Queue = state["_queue"]
    messages = list(state["messages"])
    last_msg = messages[-1]  # 必定是含 tool_calls 的 assistant 消息

    tool_results: list[dict] = []
    for tc in last_msg.get("tool_calls", []):
        name = tc["function"]["name"]
        label = TOOL_LABELS.get(name, f"正在调用 {name}")
        q.put(("status", label))
        print(f"[Agent] 调用工具: {name}")

        try:
            args = json.loads(tc["function"]["arguments"])
        except Exception:
            args = {}

        result = _run_tool(name, args)
        trimmed = _trim_tool_result(result)
        print(f"[Agent] 工具结果: {trimmed[:100]}...")

        tool_results.append({
            "role": "tool",
            "tool_call_id": tc["id"],
            "content": trimmed,
        })

    return {"messages": messages + tool_results}


# ── 条件边：决定下一个节点 ──────────────────────────────
def _should_continue(state: AgentState) -> str:
    """
    检查最新 assistant 消息是否有 tool_calls：
    - 有 → 去 run_tools 节点继续循环
    - 没有 → 结束图（END）
    同时检查轮次上限，防止死循环。
    """
    last = state["messages"][-1]
    if last.get("tool_calls") and state["rounds"] < MAX_ROUNDS:
        return "run_tools"
    return END


# ── 构建并编译图 ────────────────────────────────────────
#
#   START
#     │
#     ▼
#  call_model ──(有工具?)──→ run_tools ──┐
#     ▲                                  │
#     └──────────────────────────────────┘
#     │
#  (无工具/超轮次)
#     ▼
#    END
#
_workflow = StateGraph(AgentState)
_workflow.add_node("call_model", _node_call_model)
_workflow.add_node("run_tools",  _node_run_tools)
_workflow.set_entry_point("call_model")
_workflow.add_conditional_edges(
    "call_model",
    _should_continue,
    {"run_tools": "run_tools", END: END},
)
_workflow.add_edge("run_tools", "call_model")

_agent_graph = _workflow.compile()


# ════════════════════════════════════════════════════════
#  公共接口（与旧版保持完全兼容）
# ════════════════════════════════════════════════════════

@traceable(name="Agent Loop", run_type="chain")
def run_agent_stream(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
) -> Generator[tuple[str, str], None, None]:
    """
    流式 Agent 循环，yield (type, text)：
      ("status", "正在搜索...")   — 工具调用状态
      ("chunk",  "回复内容...")   — 最终回复内容（实时流式）

    内部使用 LangGraph 状态图；用 queue.Queue 桥接图的同步执行
    与外部 Generator 接口，保证前端流式体验不变。
    """
    # 动态注入长期记忆
    memories = get_memories()
    system = (
        SYSTEM_PROMPT + "\n\n## 关于用户的已知信息\n" + memories
        if memories else SYSTEM_PROMPT
    )
    full_messages = [{"role": "system", "content": system}] + messages

    # 用 Queue 桥接图（子线程）和 Generator（主线程）
    q: _queue.Queue = _queue.Queue()
    _DONE = object()  # 哨兵值，标记图执行完毕

    def _run_graph():
        start = time.perf_counter()
        try:
            final_state = _agent_graph.invoke({
                "messages": full_messages,
                "model": model,
                "rounds": 0,
                "_queue": q,
            })
            elapsed = time.perf_counter() - start
            print(
                f"[Agent] 完成 | 模型={model} | "
                f"轮次={final_state['rounds']} | 用时={elapsed:.2f}s"
            )
        except Exception as e:
            q.put(("chunk", f"\n\n（Agent 异常：{e}）"))
        finally:
            q.put(_DONE)  # 无论正常/异常，都发送结束信号

    # 图在子线程中运行，主线程消费队列并 yield
    threading.Thread(target=_run_graph, daemon=True).start()

    while True:
        item = q.get()
        if item is _DONE:
            break
        yield item
