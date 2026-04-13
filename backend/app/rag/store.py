"""
向量数据库 - ChromaDB + BM25 混合检索（Hybrid Search）

检索流程：
  1. 向量检索（语义相似）  → Top N
  2. BM25 检索（关键词匹配）→ Top N
  3. RRF 算法融合两路结果  → 综合 Top K
"""
import uuid
from pathlib import Path
import jieba
import chromadb
from rank_bm25 import BM25Okapi
from app.rag.embedder import DashScopeEmbedding

CHROMA_PATH = Path(__file__).resolve().parents[3] / "data" / "chroma"

_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
_embedding_fn = DashScopeEmbedding()

# 所有文档存在同一个 collection 里
collection = _client.get_or_create_collection(
    name="knowledge",
    embedding_function=_embedding_fn,
)


def add_document(text: str, source: str = "") -> int:
    """
    把文档切成小块后存入向量库。
    返回实际存入的块数。
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,   # 每块最多 500 字
        chunk_overlap=50, # 块之间重叠 50 字，避免切断语义
    )
    chunks = splitter.split_text(text)
    if not chunks:
        return 0

    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [{"source": source}] * len(chunks)
    collection.add(documents=chunks, ids=ids, metadatas=metadatas)
    return len(chunks)


def _tokenize(text: str) -> list[str]:
    """
    中文分词：用 jieba 切词，过滤单字和空白。
    BM25 需要把文本切成词列表才能做关键词匹配。
    例："今天北京天气" → ["今天", "北京", "天气"]
    """
    return [w for w in jieba.cut(text) if len(w.strip()) > 1]


def _rrf(rankings: list[list[str]], k: int = 60) -> list[str]:
    """
    RRF（Reciprocal Rank Fusion）多路检索结果融合。

    原理：每个文档的得分 = Σ 1/(rank_i + k)
    - rank_i 是该文档在第 i 路结果中的排名（从 1 开始）
    - k=60 是经验常数，防止第一名得分过于悬殊
    - 在多路中都靠前的文档，总分最高

    示例（两路各 3 个结果，k=60）：
      文档 A：向量第1名(1/61) + BM25第2名(1/62) = 0.0326
      文档 B：向量第2名(1/62) + BM25第1名(1/61) = 0.0326
      文档 C：向量第3名(1/63) + BM25不存在(0)   = 0.0159
    """
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (rank + k)
    # 按总分降序，返回文档 id 列表
    return sorted(scores, key=lambda x: scores[x], reverse=True)


def search_knowledge(query: str, n_results: int = 5) -> str:
    """
    混合检索：向量检索 + BM25，用 RRF 融合，返回最相关的文档片段。

    相比纯向量检索的改进：
    - 向量：擅长语义相似（"API接口" ≈ "端点"）
    - BM25：擅长精确关键词（搜索词原文出现得分高）
    - 两路互补，召回率更高
    """
    total = collection.count()
    if total == 0:
        return "知识库为空，请先添加文档。"

    # 获取所有文档（BM25 需要在全量文档上建索引）
    all_data = collection.get(include=["documents", "metadatas"])
    all_ids: list[str] = all_data["ids"]
    all_docs: list[str] = all_data["documents"]
    all_metas: list[dict] = all_data["metadatas"]

    candidate_n = min(n_results * 3, total)  # 每路多取一些，再融合精排

    # ── 路 1：向量检索 ───────────────────────────────────
    vec_results = collection.query(
        query_texts=[query],
        n_results=candidate_n,
    )
    vec_ids: list[str] = vec_results["ids"][0]

    # ── 路 2：BM25 关键词检索 ────────────────────────────
    # 对所有文档分词，建 BM25 索引
    tokenized_docs = [_tokenize(doc) for doc in all_docs]
    bm25 = BM25Okapi(tokenized_docs)

    # 对查询分词，计算每个文档的 BM25 分数
    query_tokens = _tokenize(query)
    bm25_scores = bm25.get_scores(query_tokens)

    # 取分数最高的 candidate_n 个文档的 id
    top_indices = sorted(
        range(len(bm25_scores)),
        key=lambda i: bm25_scores[i],
        reverse=True,
    )[:candidate_n]
    bm25_ids: list[str] = [all_ids[i] for i in top_indices]

    # ── RRF 融合两路结果 ─────────────────────────────────
    fused_ids = _rrf([vec_ids, bm25_ids])[:n_results]

    # ── 按融合排序拼接结果 ───────────────────────────────
    id_to_doc  = dict(zip(all_ids, all_docs))
    id_to_meta = dict(zip(all_ids, all_metas))

    parts = []
    for doc_id in fused_ids:
        doc = id_to_doc.get(doc_id, "")
        src = id_to_meta.get(doc_id, {}).get("source", "")
        label = f"[来源: {src}] " if src else ""
        parts.append(f"{label}{doc}")

    return "\n\n---\n\n".join(parts)


def list_sources() -> list[str]:
    """列出知识库中所有文档来源"""
    if collection.count() == 0:
        return []
    results = collection.get(include=["metadatas"])
    sources = {m.get("source", "") for m in results["metadatas"]}
    return sorted(s for s in sources if s)


def delete_source(source: str):
    """删除某个来源的所有文档块"""
    results = collection.get(where={"source": source}, include=["metadatas"])
    if results["ids"]:
        collection.delete(ids=results["ids"])
