"""
工具函数测试
"""
from app.tools import search_web, read_file, write_file, run_python_code


def test_write_and_read_file():
    write_file("test_note.txt", "hello world")
    content = read_file("test_note.txt")
    assert content == "hello world"


def test_read_nonexistent_file():
    result = read_file("not_exists.txt")
    assert "不存在" in result


def test_file_path_traversal_blocked():
    """不允许访问 data/ 目录之外的文件"""
    import pytest
    with pytest.raises(ValueError):
        read_file("../../.env")


def test_run_python_code():
    result = run_python_code("print('hello')")
    assert "hello" in result


def test_run_python_code_with_calc():
    result = run_python_code("print(1 + 2)")
    assert "3" in result


def test_run_python_code_error():
    result = run_python_code("raise ValueError('oops')")
    assert "执行错误" in result


def test_search_web():
    result = search_web("Python programming")
    # 只验证能返回内容，不验证具体文字（网络结果会变）
    assert len(result) > 10
