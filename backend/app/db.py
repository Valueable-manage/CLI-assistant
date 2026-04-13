"""
SQLite 数据库 - 会话与消息持久化
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "chat.db"


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 让查询结果可以用列名访问
    return conn


def init_db():
    """建表（首次启动时执行）"""
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id       TEXT PRIMARY KEY,
                title    TEXT NOT NULL DEFAULT '新对话',
                created_at DATETIME DEFAULT (datetime('now','localtime')),
                updated_at DATETIME DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS messages (
                id         TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role       TEXT NOT NULL,
                content    TEXT NOT NULL,
                created_at DATETIME DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS memories (
                id         TEXT PRIMARY KEY,
                content    TEXT NOT NULL,
                created_at DATETIME DEFAULT (datetime('now','localtime'))
            );
        """)
