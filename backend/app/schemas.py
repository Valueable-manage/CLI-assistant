"""
API 请求/响应模型
"""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(..., min_length=1, max_length=64_000)
    model: str | None = None
