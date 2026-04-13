"""
图片分析 - 使用 qwen-vl-plus 视觉模型
"""
import base64
from openai import OpenAI
from app.config import API_KEY, BASE_URL

_client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

MIME_MAP = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg",
    "png": "image/png",  "gif": "image/gif",
    "webp": "image/webp", "bmp": "image/bmp",
}

IMAGE_EXTS = set(MIME_MAP.keys())


def analyze_image(image_bytes: bytes, filename: str = "") -> str:
    """把图片发给视觉模型，返回详细描述"""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpeg"
    mime = MIME_MAP.get(ext, "image/jpeg")
    b64 = base64.b64encode(image_bytes).decode()
    data_url = f"data:{mime};base64,{b64}"

    response = _client.chat.completions.create(
        model="qwen-vl-plus",
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": data_url}},
                {"type": "text", "text": "请详细描述这张图片的内容，包括文字、图表、主要元素等所有信息。"},
            ],
        }],
    )
    return response.choices[0].message.content
