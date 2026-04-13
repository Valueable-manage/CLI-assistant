"""
网页搜索工具 - 获取实时信息（Tavily，专为 AI 设计的搜索 API）
"""
import os
from tavily import TavilyClient

_client: TavilyClient | None = None


def _get_client() -> TavilyClient:
    global _client
    if _client is None:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise RuntimeError("TAVILY_API_KEY 未设置")
        _client = TavilyClient(api_key=api_key)
    return _client


_MAX_CONTENT_PER_RESULT = 800   # 每条搜索结果最多保留的字符数
_MAX_TOTAL = 3000               # 搜索结果总字符上限


def search_web(query: str, max_results: int = 3) -> str:
    """搜索网页，返回前几条结果的标题和摘要"""
    client = _get_client()
    response = client.search(query, max_results=max_results)
    results = response.get("results", [])
    if not results:
        return "未找到相关结果"
    parts = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "")
        content = r.get("content", "")
        if len(content) > _MAX_CONTENT_PER_RESULT:
            content = content[:_MAX_CONTENT_PER_RESULT] + "…"
        parts.append(f"{i}. {title}\n{content}")
    result = "\n\n".join(parts)
    if len(result) > _MAX_TOTAL:
        result = result[:_MAX_TOTAL] + "\n…（已截断）"
    return result
