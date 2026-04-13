"""
工具模块 - 网页搜索、文件读写、代码执行、知识库检索、数据库查询
"""
from .search import search_web
from .file_tool import read_file, write_file
from .run_code import run_python_code
from .db_query import query_database
from app.rag.store import search_knowledge

# OpenAI function calling 格式的工具描述，Agent 循环时传给 LLM
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "搜索网页获取实时信息，适用于天气、新闻、最新数据等问题",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取 data/ 目录下的文件内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "相对于 data/ 目录的文件路径，如 notes.txt"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "将内容写入 data/ 目录下的文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "相对于 data/ 目录的文件路径，如 notes.txt"},
                    "content": {"type": "string", "description": "要写入的内容"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_python_code",
            "description": "执行 Python 代码并返回输出结果",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "要执行的 Python 代码"},
                },
                "required": ["code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_database",
            "description": (
                "查询本地 SQLite 数据库，适用于：统计对话次数、查看历史话题、"
                "分析消息数量等结构化数据查询。只支持 SELECT 语句。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "要执行的 SELECT SQL 语句",
                    },
                },
                "required": ["sql"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "在个人知识库中搜索，适用于查询你自己保存的笔记、文档、资料等私有内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词或问题"},
                },
                "required": ["query"],
            },
        },
    },
]

TOOL_FUNCTIONS = {
    "search_web": search_web,
    "read_file": read_file,
    "write_file": write_file,
    "run_python_code": run_python_code,
    "query_database": query_database,
    "search_knowledge": search_knowledge,
}
