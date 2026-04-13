"""
聊天 API - 带后端 session 记忆（SQLite）
"""
import logging
import json as _json
import threading

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse

from app.config import DEFAULT_MODEL, ALLOWED_MODELS, ALLOWED_IDS
from app.schemas import ChatRequest
from app.agent.core import run_agent_stream
from app.agent.researcher import run_research_stream
from app.memory import (
    create_session, list_sessions, delete_session,
    add_message, get_messages, touch_session, update_session_title,
    search_sessions,
)
from app.long_memory import extract_and_save
from app.rag.parser import parse_file
from app.vision import analyze_image, IMAGE_EXTS

router = APIRouter(prefix="/api", tags=["chat"])
logger = logging.getLogger(__name__)


@router.get("/models")
async def api_list_models():
    return {"models": ALLOWED_MODELS, "default": DEFAULT_MODEL}


# ── 会话管理 ───────────────────────────────────────

@router.get("/sessions")
async def api_list_sessions():
    return {"sessions": list_sessions()}


@router.delete("/sessions/{session_id}")
async def api_delete_session(session_id: str):
    delete_session(session_id)
    return {"ok": True}


@router.get("/sessions/{session_id}/messages")
async def api_get_messages(session_id: str):
    return {"messages": get_messages(session_id)}


@router.get("/search")
async def api_search(q: str = ""):
    if not q.strip():
        return {"sessions": []}
    return {"sessions": search_sessions(q.strip())}


# ── 公共流式生成逻辑 ────────────────────────────────

def _make_stream(session_id: str, user_message: str, history: list[dict], model: str):
    def generate():
        reply_parts = []
        for ev_type, ev_text in run_agent_stream(history, model=model):
            reply_parts.append(ev_text if ev_type == "chunk" else "")
            yield _json.dumps({"t": ev_type, "v": ev_text}, ensure_ascii=False) + "\n"

        reply = "".join(reply_parts)
        add_message(session_id, "user", user_message)
        add_message(session_id, "assistant", reply)

        if len(history) == 1:
            title = user_message[:20] + ("..." if len(user_message) > 20 else "")
            update_session_title(session_id, title)

        touch_session(session_id)

        # 对话结束后，后台提取记忆（不阻塞响应返回）
        # 把 assistant 回复也加入 history，让 LLM 看到完整对话再判断
        full_history = history + [{"role": "assistant", "content": reply}]
        threading.Thread(
            target=extract_and_save,
            args=(full_history,),
            daemon=True,
        ).start()

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


# ── 普通对话 ───────────────────────────────────────

@router.post("/chat")
async def chat(req: ChatRequest):
    model = DEFAULT_MODEL
    if req.model and req.model in ALLOWED_IDS:
        model = req.model

    create_session(req.session_id)
    history = get_messages(req.session_id)
    history.append({"role": "user", "content": req.message})

    return _make_stream(req.session_id, req.message, history, model)


# ── 深度研究模式 ────────────────────────────────────

@router.post("/chat/research")
async def chat_research(req: ChatRequest):
    """深度研究接口：Multi-Agent 并行搜索 + 报告整合"""
    model = DEFAULT_MODEL
    if req.model and req.model in ALLOWED_IDS:
        model = req.model

    create_session(req.session_id)

    def generate():
        is_first = len(get_messages(req.session_id)) == 0  # 在存消息之前判断
        reply_parts = []
        for ev_type, ev_text in run_research_stream(req.message, model=model):
            reply_parts.append(ev_text if ev_type == "chunk" else "")
            yield _json.dumps({"t": ev_type, "v": ev_text}, ensure_ascii=False) + "\n"

        reply = "".join(reply_parts)
        add_message(req.session_id, "user", req.message)
        add_message(req.session_id, "assistant", reply)

        if is_first:
            title = req.message[:20] + ("..." if len(req.message) > 20 else "")
            update_session_title(req.session_id, title)

        touch_session(req.session_id)

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


# ── 带文件的对话 ────────────────────────────────────

@router.post("/chat/with-files")
async def chat_with_files(
    session_id: str = Form(...),
    message: str = Form(default=""),
    model: str | None = Form(None),
    files: list[UploadFile] = File(default=[]),
):
    resolved_model = DEFAULT_MODEL
    if model and model in ALLOWED_IDS:
        resolved_model = model

    create_session(session_id)

    # 处理每个附件，提取内容
    file_contexts: list[str] = []
    for upload in files:
        raw = await upload.read()
        fname = upload.filename or "未知文件"
        ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""

        if ext in IMAGE_EXTS:
            yield_status = f"正在分析图片 {fname}..."
            try:
                desc = analyze_image(raw, fname)
                file_contexts.append(f"[图片：{fname}]\n{desc}")
            except Exception as e:
                file_contexts.append(f"[图片：{fname}] 分析失败：{e}")
        else:
            try:
                text = parse_file(fname, raw)
                file_contexts.append(f"[文件：{fname}]\n{text[:4000]}")  # 截断避免超长
            except ValueError as e:
                file_contexts.append(f"[文件：{fname}] 解析失败：{e}")

    # 把文件内容拼入用户消息
    if file_contexts:
        combined = "\n\n---\n\n".join(file_contexts)
        full_message = f"{combined}\n\n---\n\n用户问题：{message}" if message.strip() else combined
    else:
        full_message = message

    history = get_messages(session_id)
    history.append({"role": "user", "content": full_message})

    return _make_stream(session_id, message, history, resolved_model)
