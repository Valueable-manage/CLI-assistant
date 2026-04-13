"""
应用配置 - 环境变量与常量
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# 加载 backend/.env 和根目录 .env
load_dotenv()
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "你是一个聪明、简洁的个人助手，回答简明扼要，有条理。")

# ── 云端配置（DashScope，OpenAI 兼容接口）──────────────
CLOUD_API_KEY = os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
CLOUD_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# ── 本地配置（Ollama）─────────────────────────────────
# Ollama 不需要真实 key，但 openai SDK 要求非空
LOCAL_API_KEY  = "ollama"
LOCAL_BASE_URL = os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434/v1"

# ── 默认模型 ──────────────────────────────────────────
DEFAULT_MODEL = os.getenv("OPENAI_MODEL") or "qwen3.5-plus"

# 兼容旧字段（BASE_URL / API_KEY 仍可被外部读取）
API_KEY  = CLOUD_API_KEY
BASE_URL = CLOUD_BASE_URL

# ── 允许客户端选择的模型列表（后端为单一事实来源）────────
_CLOUD_MODELS = {
    "qwen3.5-plus-2026-02-15": "Qwen3.5-Plus-2026-02-15",
    "qwen3.5-plus": "Qwen3.5-Plus",
    "qwen-turbo":   "Qwen-Turbo",
}

# 本地模型 — 需先执行 `ollama pull <模型名>`
_LOCAL_MODELS = {
    "qwen2.5:7b": "Qwen2.5-7B（本地）",
}

LOCAL_MODEL_IDS = set(_LOCAL_MODELS.keys())  # 用于判断是否走 Ollama

ALLOWED_MODELS = (
    [{"id": k, "name": v, "type": "cloud"} for k, v in _CLOUD_MODELS.items()]
    + [{"id": k, "name": v, "type": "local"} for k, v in _LOCAL_MODELS.items()]
)

ALLOWED_IDS = {m["id"] for m in ALLOWED_MODELS}
