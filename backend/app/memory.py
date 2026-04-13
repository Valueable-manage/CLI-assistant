"""
会话记忆 - 读写 SQLite
"""
import uuid
from app.db import get_conn


# ── 会话 ──────────────────────────────────────────

def create_session(session_id: str, title: str = "新对话"):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO sessions (id, title) VALUES (?, ?)",
            (session_id, title),
        )


def list_sessions() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, title, updated_at FROM sessions ORDER BY updated_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def delete_session(session_id: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))


def update_session_title(session_id: str, title: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE sessions SET title = ? WHERE id = ?",
            (title, session_id),
        )


def touch_session(session_id: str):
    """更新 updated_at，让该会话排到列表最前"""
    with get_conn() as conn:
        conn.execute(
            "UPDATE sessions SET updated_at = datetime('now','localtime') WHERE id = ?",
            (session_id,),
        )


# ── 消息 ──────────────────────────────────────────

def add_message(session_id: str, role: str, content: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO messages (id, session_id, role, content) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), session_id, role, content),
        )


def get_messages(session_id: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY created_at",
            (session_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def search_sessions(q: str) -> list[dict]:
    """搜索会话标题或消息内容，返回匹配的会话列表（附首条匹配消息片段）"""
    pattern = f"%{q}%"
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT s.id, s.title, s.updated_at,
                   (SELECT substr(content, 1, 80)
                    FROM messages
                    WHERE session_id = s.id AND content LIKE ?
                    ORDER BY created_at LIMIT 1) AS snippet
            FROM sessions s
            WHERE s.title LIKE ?
               OR EXISTS (
                   SELECT 1 FROM messages m
                   WHERE m.session_id = s.id AND m.content LIKE ?
               )
            ORDER BY s.updated_at DESC
            """,
            (pattern, pattern, pattern),
        ).fetchall()
    return [dict(r) for r in rows]
