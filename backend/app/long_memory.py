"""
长期记忆 - 跨会话的用户信息提取与注入
"""
import uuid
import logging
from openai import OpenAI
from app.db import get_conn
from app.config import CLOUD_API_KEY, CLOUD_BASE_URL, DEFAULT_MODEL

logger = logging.getLogger(__name__)

# 用云端模型做记忆提取（小任务，不走 Agent 循环）
_client = OpenAI(api_key=CLOUD_API_KEY or "placeholder", base_url=CLOUD_BASE_URL)

# 记忆提取的 Prompt：明确告诉 LLM 只提取用户相关信息，没有就返回空
_EXTRACT_PROMPT = """\
你是一个记忆提取助手。阅读下面的对话，判断其中是否包含值得长期记住的用户个人信息。

值得记住的信息包括：
- 用户的技能水平（如"Python 初学者"、"有 5 年后端经验"）
- 用户的偏好（如"喜欢简洁的代码风格"、"不喜欢过多注释"）
- 用户的背景（如"正在学习 AI 开发"、"主要用 Windows"）
- 用户明确告知的事实（如"我的项目叫 CLI-assistant"）

不值得记住的信息：
- 临时性问题（天气、新闻等）
- 纯技术讨论（没有涉及用户个人情况）
- 闲聊

如果有值得记住的信息，请用一句话提取出来（不超过 50 字）。
如果没有，只回复"无"，不要解释。
"""


def save_memory(content: str) -> None:
    """写入一条记忆"""
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO memories (id, content) VALUES (?, ?)",
            (str(uuid.uuid4()), content),
        )


def get_memories() -> str:
    """读取所有记忆，返回拼接后的字符串；无记忆时返回空字符串"""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT content FROM memories ORDER BY created_at"
        ).fetchall()
    if not rows:
        return ""
    return "\n".join(f"- {r['content']}" for r in rows)


def extract_and_save(history: list[dict], model: str = DEFAULT_MODEL) -> None:
    """
    对话结束后调用：让 LLM 判断是否有值得记忆的信息，有则存入数据库。
    使用云端模型，避免本地小模型提取质量差。
    失败时静默处理，不影响主流程。
    """
    # 只取最近 6 条消息，避免 token 过多（记忆提取不需要全部上下文）
    recent = history[-6:]
    conversation = "\n".join(
        f"{'用户' if m['role'] == 'user' else '助手'}：{m['content'][:200]}"
        for m in recent
    )

    try:
        resp = _client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _EXTRACT_PROMPT},
                {"role": "user", "content": f"对话内容：\n{conversation}"},
            ],
            max_tokens=100,
            temperature=0,  # 温度设 0，提取结果更稳定
        )
        result = resp.choices[0].message.content.strip()

        # "无" 或空字符串表示没有值得记忆的内容
        if result and result != "无":
            save_memory(result)
            logger.info(f"[Memory] 保存记忆：{result}")

    except Exception as e:
        # 记忆提取失败不影响正常对话
        logger.warning(f"[Memory] 提取失败：{e}")
