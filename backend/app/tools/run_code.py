"""
代码执行工具 - 运行 Python 代码并返回结果
"""
import subprocess
import sys
import os
from pathlib import Path

# 代码运行目录：项目根目录，data/ 文件夹在此处，open('data/xxx') 可直接访问
_PROJECT_ROOT = Path(__file__).resolve().parents[3]

# 强制 UTF-8 输出，避免 Windows GBK 编码导致 UnicodeEncodeError
_ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}


def run_python_code(code: str, timeout: int = 30) -> str:
    """执行 Python 代码，返回标准输出或错误信息。
    工作目录为项目根目录，文件路径写 data/filename 即可。
    """
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout,
        cwd=str(_PROJECT_ROOT),
        env=_ENV,
    )
    if result.returncode == 0:
        return result.stdout or "（代码执行成功，无输出）"
    return f"执行错误:\n{result.stderr}"
