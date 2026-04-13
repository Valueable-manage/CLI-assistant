"""
RAGAS 评估脚本 - 量化 RAG 系统质量

运行方式（在 backend 目录）：
    uv run python tests/eval_rag.py

评估流程：
  1. 对每个问题，用 search_knowledge 检索相关文档块
  2. 用 LLM 根据检索内容生成回答
  3. RAGAS 用 LLM 当裁判，对比标准答案，输出四个指标分数
"""
import sys
import os
from pathlib import Path

# 加载根目录 .env
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# 让 Python 能找到 app 模块
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from openai import OpenAI
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    context_recall,
    context_precision,
)
from ragas.llms import LangchainLLMWrapper
from langchain_openai import ChatOpenAI

from app.rag.store import search_knowledge

# ── 评估数据集（问题 + 标准答案）──────────────────────────
# 这是"黄金答案"，人工写的，RAGAS 用它来评判 AI 回答质量
# 针对简历内容设计：覆盖语义问题、精确词、混合型

EVAL_DATA = [
    {
        "question": "候选人有哪些 AI 相关技术能力？",
        "ground_truth": (
            "熟练使用 Python 进行 LLM 应用开发；"
            "掌握 LangChain / LlamaIndex 构建 Agent 与 RAG 系统；"
            "熟悉向量数据库（Chroma、Pinecone）及 Embedding 技术；"
            "具备 Claude / OpenAI API 调用与 Prompt Engineering 实战经验；"
            "熟悉 Google Cloud Platform。"
        ),
    },
    {
        "question": "候选人的语言能力如何？",
        "ground_truth": "英语具备基础沟通能力；韩语 TOPIK 四级，可进行日常会话。",
    },
    {
        "question": "NovelWander 项目是做什么的？",
        "ground_truth": (
            "基于生成式 AI 的在线文学平台，利用大语言模型对中国奇幻小说进行改写，"
            "向全球读者传播中国玄幻文学内容，累计注册用户约 1000 人。"
        ),
    },
    {
        "question": "候选人在哪所大学就读？专业是什么？",
        "ground_truth": "国立釜庆大学（Pukyong National University），计算机科学学士，2018-2025年，韩国釜山。",
    },
    {
        "question": "候选人有哪些云平台部署经验？",
        "ground_truth": (
            "使用 Docker 容器化应用并在 Google Cloud Platform（GCP）完成服务部署；"
            "配置基础 CI/CD 流程；曾探索阿里云部署方案。"
        ),
    },
]


def build_rag_answer(question: str, contexts: list[str]) -> str:
    """根据检索到的文档块，用 LLM 生成回答"""
    client = OpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    context_text = "\n\n".join(contexts)
    resp = client.chat.completions.create(
        model="qwen3.5-plus",
        messages=[
            {"role": "system", "content": "根据提供的文档内容回答问题，只使用文档中的信息。"},
            {"role": "user", "content": f"文档内容：\n{context_text}\n\n问题：{question}"},
        ],
        max_tokens=300,
        temperature=0,
    )
    return resp.choices[0].message.content.strip()


def main():
    print("=" * 60)
    print("RAGAS 评估开始")
    print("=" * 60)

    # ── 构建评估数据 ──────────────────────────────────────
    questions, answers, contexts, ground_truths = [], [], [], []

    for item in EVAL_DATA:
        q = item["question"]
        print(f"\n处理问题：{q}")

        # 1. 用混合检索获取相关文档块
        raw = search_knowledge(q, n_results=3)
        ctx_list = [c.strip() for c in raw.split("---") if c.strip()]
        print(f"  检索到 {len(ctx_list)} 个文档块")

        # 2. 用 LLM 生成回答
        answer = build_rag_answer(q, ctx_list)
        print(f"  生成回答：{answer[:60]}...")

        questions.append(q)
        answers.append(answer)
        contexts.append(ctx_list)
        ground_truths.append(item["ground_truth"])

    # ── 构建 RAGAS Dataset ────────────────────────────────
    dataset = Dataset.from_dict({
        "question":    questions,
        "answer":      answers,
        "contexts":    contexts,
        "ground_truth": ground_truths,
    })

    # ── 配置 RAGAS 使用 DashScope（OpenAI 兼容）────────────
    # RAGAS 内部用 LLM 当裁判打分，需要给它配置模型
    langchain_llm = ChatOpenAI(
        model="qwen3.5-plus",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        temperature=0,
    )
    ragas_llm = LangchainLLMWrapper(langchain_llm)

    # ── 跑评估 ────────────────────────────────────────────
    # 只跑纯 LLM 评估的三个指标（不需要 embedding API）
    # faithfulness:      回答有没有编造
    # context_recall:    检索有没有漏掉关键内容
    # context_precision: 检索结果里有用内容占比
    print("\n\n开始 RAGAS 评估（需要多次调用 LLM，约 1-2 分钟）...")
    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, context_recall, context_precision],
        llm=ragas_llm,
    )

    # ── 打印结果 ──────────────────────────────────────────
    print("\n" + "=" * 60)
    print("评估结果")
    print("=" * 60)
    df = result.to_pandas()
    print(df.columns.tolist())  # 打印实际列名，方便调试

    metrics = ["faithfulness", "context_recall", "context_precision"]
    # 只显示存在的列
    available = [m for m in metrics if m in df.columns]
    if available:
        print(df[available].to_string(index=False))

    print("\n平均分：")
    for metric in available:
        avg = df[metric].mean()
        bar = "█" * int(avg * 20)
        print(f"  {metric:<22} {avg:.3f}  {bar}")

    print("\n指标说明：")
    print("  faithfulness      回答忠实度（有没有编造）")
    print("  context_recall    检索召回率（有没有漏掉关键内容）")
    print("  context_precision 检索精确率（结果里有多少是有用的）")


if __name__ == "__main__":
    main()
