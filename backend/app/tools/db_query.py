"""
数据库查询工具 - 只允许 SELECT，防止误操作破坏数据
"""
import re
from app.db import get_conn

# 危险关键词黑名单（不区分大小写）
# 即使以 SELECT 开头，包含这些词也拒绝执行
_DANGEROUS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|REPLACE|ATTACH|DETACH)\b",
    re.IGNORECASE,
)

MAX_ROWS = 50  # 最多返回行数，防止结果太长撑爆 Prompt


def query_database(sql: str) -> str:
    """
    执行只读 SQL 查询，返回格式化的文本结果。

    安全规则：
    1. 只允许 SELECT 语句
    2. 禁止包含任何写操作关键词
    3. 最多返回 50 行
    """
    sql = sql.strip()

    # 规则1：必须以 SELECT 开头
    if not sql.upper().startswith("SELECT"):
        return "❌ 只允许执行 SELECT 查询语句。"

    # 规则2：不能包含危险关键词
    if _DANGEROUS.search(sql):
        return "❌ 查询语句包含不允许的操作关键词。"

    try:
        with get_conn() as conn:
            # 设置只读模式，数据库层面再加一层保险
            conn.execute("PRAGMA query_only = ON")
            cursor = conn.execute(sql)
            rows = cursor.fetchmany(MAX_ROWS)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

        if not rows:
            return "查询结果为空。"

        # 格式化为表格文本，方便 LLM 理解
        header = " | ".join(columns)
        separator = "-" * len(header)
        lines = [header, separator]
        for row in rows:
            lines.append(" | ".join(str(v) if v is not None else "NULL" for v in row))

        result = "\n".join(lines)

        # 如果达到上限，提示用户结果可能被截断
        if len(rows) == MAX_ROWS:
            result += f"\n\n（结果已截断，最多显示 {MAX_ROWS} 行，请用 WHERE 或 LIMIT 缩小范围）"

        return result

    except Exception as e:
        return f"❌ SQL 执行出错：{e}"
