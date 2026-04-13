"""
知识库管理 API - 添加、查询、删除文档
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from app.rag.store import add_document, list_sources, delete_source
from app.rag.parser import parse_file

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


class AddDocRequest(BaseModel):
    text: str = Field(..., min_length=1)
    source: str = Field(default="", description="来源标注，如文件名或网址")


@router.post("/add")
async def api_add_document(req: AddDocRequest):
    chunks = add_document(req.text, req.source)
    return {"ok": True, "chunks": chunks}


@router.post("/upload")
async def api_upload_file(file: UploadFile = File(...)):
    """上传文件，自动解析后存入知识库"""
    content = await file.read()
    try:
        text = parse_file(file.filename or "", content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not text.strip():
        raise HTTPException(status_code=400, detail="文件内容为空")
    chunks = add_document(text, source=file.filename or "上传文件")
    return {"ok": True, "chunks": chunks, "source": file.filename}


@router.get("/sources")
async def api_list_sources():
    return {"sources": list_sources()}


@router.delete("/sources/{source}")
async def api_delete_source(source: str):
    delete_source(source)
    return {"ok": True}
