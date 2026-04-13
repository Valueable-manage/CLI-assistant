"""
Multi-Agent 深度研究图

架构：Supervisor 模式
  supervisor → search（并行3路）→ writer → END

Queue 传递方案：module-level dict，用 run_id 做 key
  - state 里只放 run_id（字符串，可序列化）
  - 节点通过 run_id 从全局 dict 拿到 Queue
  - 请求结束后清理
"""
import json
import queue as _queue
import threading
import time
import uuid
from typing import TypedDict

from langgraph.graph import END, StateGraph
from openai import OpenAI
from langsmith.wrappers import wrap_openai

from app.config import CLOUD_API_KEY, CLOUD_BASE_URL, DEFAULT_MODEL
from app.tools import TOOL_FUNCTIONS

_client = wrap_openai(OpenAI(api_key=CLOUD_API_KEY or "placeholder", base_url=CLOUD_BASE_URL))

# run_id → Queue，支持并发多个研究请求
_queues: dict[str, _queue.Queue] = {}
_queues_lock = threading.Lock()


def _q(run_id: str) -> _queue.Queue:
    return _queues[run_id]


# ════════════════════════════════════════════════════════
#  状态（全部可序列化）
# ════════════════════════════════════════════════════════

class ResearchState(TypedDict):
    run_id: str                 # 用于从全局 dict 找到对应 Queue
    question: str
    model: str
    search_queries: list[str]
    search_results: list[str]
    report: str


# ════════════════════════════════════════════════════════
#  节点
# ════════════════════════════════════════════════════════

def _node_supervisor(state: ResearchState) -> dict:
    q = _q(state["run_id"])
    q.put(("status", "正在拆解研究任务..."))

    resp = _client.chat.completions.create(
        model=state["model"],
        messages=[
            {
                "role": "system",
                "content": (
                    "你是一个研究任务规划师。"
                    "把用户的问题拆解成 3 个独立的搜索关键词，覆盖不同角度。"
                    "只输出 JSON 数组，不要输出其他内容。"
                    '示例：["关键词1", "关键词2", "关键词3"]'
                ),
            },
            {"role": "user", "content": f"研究问题：{state['question']}"},
        ],
        temperature=0,
        timeout=90,  # supervisor 只生成关键词，90 秒足够
    )

    raw = resp.choices[0].message.content.strip()
    try:
        start = raw.index("[")
        end = raw.rindex("]") + 1
        queries = json.loads(raw[start:end])
    except Exception:
        queries = [state["question"]]

    print(f"[Researcher] 搜索词：{queries}")
    q.put(("status", f"已拆解为 {len(queries)} 个搜索方向：{'、'.join(queries)}"))
    return {"search_queries": queries}


def _node_search(state: ResearchState) -> dict:
    q = _q(state["run_id"])
    queries = state["search_queries"]
    results: list[str | None] = [None] * len(queries)
    search_fn = TOOL_FUNCTIONS["search_web"]

    def _do_search(idx: int, query: str):
        t0 = time.perf_counter()
        q.put(("status", f"搜索中（{idx+1}/{len(queries)}）：{query}"))
        try:
            result = search_fn(query=query)
            results[idx] = f"【{query}】\n{result}"
            elapsed = time.perf_counter() - t0
            print(f"[Researcher] 搜索完成：{query} | 用时={elapsed:.2f}s")
        except Exception as e:
            results[idx] = f"【{query}】搜索失败：{e}"
            print(f"[Researcher] 搜索失败：{query} | {e}")

    threads = [
        threading.Thread(target=_do_search, args=(i, q_text), daemon=True)
        for i, q_text in enumerate(queries)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    return {"search_results": [r for r in results if r]}


def _node_writer(state: ResearchState) -> dict:
    q = _q(state["run_id"])
    q.put(("status", "正在整合搜索结果，生成报告..."))

    context = "\n\n".join(state["search_results"])
    resp = _client.chat.completions.create(
        model=state["model"],
        messages=[
            {
                "role": "system",
                "content": (
                    "你是一个专业研究报告撰写员。"
                    "根据提供的搜索结果，生成一份结构清晰的研究报告。"
                    "报告格式：\n"
                    "## 研究主题\n## 核心发现\n## 详细分析\n## 总结\n"
                    "内容要准确、有深度，不要编造搜索结果中没有的信息。"
                ),
            },
            {
                "role": "user",
                "content": f"研究问题：{state['question']}\n\n搜索结果：\n{context}",
            },
        ],
        temperature=0.3,
        timeout=120,  # writer 整合内容多，给 120 秒
    )

    report = resp.choices[0].message.content.strip()
    q.put(("chunk", report))
    return {"report": report}


# ════════════════════════════════════════════════════════
#  构建图
# ════════════════════════════════════════════════════════

_workflow = StateGraph(ResearchState)
_workflow.add_node("supervisor", _node_supervisor)
_workflow.add_node("search",     _node_search)
_workflow.add_node("writer",     _node_writer)
_workflow.set_entry_point("supervisor")
_workflow.add_edge("supervisor", "search")
_workflow.add_edge("search",     "writer")
_workflow.add_edge("writer",     END)
_research_graph = _workflow.compile()


# ════════════════════════════════════════════════════════
#  公共接口
# ════════════════════════════════════════════════════════

def run_research_stream(question: str, model: str = DEFAULT_MODEL):
    run_id = uuid.uuid4().hex
    q: _queue.Queue = _queue.Queue()
    _DONE = object()

    with _queues_lock:
        _queues[run_id] = q

    start = time.perf_counter()

    def _run():
        try:
            _research_graph.invoke({
                "run_id": run_id,
                "question": question,
                "model": model,
                "search_queries": [],
                "search_results": [],
                "report": "",
            })
            elapsed = time.perf_counter() - start
            print(
                f"[Researcher] 完成 | 模型={model} | 用时={elapsed:.2f}s"
            )
        except Exception as e:
            q.put(("chunk", f"\n\n研究过程出错：{e}"))
            print(f"[Researcher] 出错：{e}")
        finally:
            q.put(_DONE)
            with _queues_lock:
                _queues.pop(run_id, None)

    threading.Thread(target=_run, daemon=True).start()

    while True:
        item = q.get()
        if item is _DONE:
            break
        yield item
