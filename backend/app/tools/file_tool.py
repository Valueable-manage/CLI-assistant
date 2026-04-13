"""
文件读写工具 - 读取/写入本地文件
"""
from pathlib import Path

# 限制只能访问这个目录下的文件，防止读取系统敏感文件
ALLOWED_DIR = Path(__file__).resolve().parents[3] / "data"


def _safe_path(path: str) -> Path:
    """确保路径在 ALLOWED_DIR 内"""
    target = (ALLOWED_DIR / path).resolve()
    if not target.is_relative_to(ALLOWED_DIR):
        raise ValueError(f"不允许访问该路径: {path}")
    return target


def read_file(path: str) -> str:
    """读取文件内容，路径相对于 data/ 目录"""
    target = _safe_path(path)
    if not target.exists():
        return f"文件不存在: {path}"
    return target.read_text(encoding="utf-8")


def write_file(path: str, content: str) -> str:
    """写入文件，路径相对于 data/ 目录，目录不存在时自动创建"""
    target = _safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"已写入: {path}"
