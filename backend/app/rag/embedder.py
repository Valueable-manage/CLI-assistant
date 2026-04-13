"""
Embedding - 把文字转成向量（使用 DashScope text-embedding-v3）
"""
from chromadb import EmbeddingFunction, Embeddings
from openai import OpenAI
from app.config import API_KEY, BASE_URL

_client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

EMBED_MODEL = "text-embedding-v3"


class DashScopeEmbedding(EmbeddingFunction):
    """让 ChromaDB 使用 DashScope 的 Embedding API"""

    def __call__(self, input: list[str]) -> Embeddings:
        response = _client.embeddings.create(
            model=EMBED_MODEL,
            input=input,
        )
        return [item.embedding for item in response.data]
