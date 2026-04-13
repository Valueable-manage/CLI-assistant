"""
FastAPI 入口 - API 服务
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.knowledge import router as knowledge_router
from app.db import init_db

app = FastAPI(title="个人助手 API")
init_db()  # 首次启动时建表
app.include_router(chat_router)
app.include_router(knowledge_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}
