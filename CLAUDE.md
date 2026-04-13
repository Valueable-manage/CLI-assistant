# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作时提供指引。

## 项目概述

两层架构的个人 AI 助手：
- **前端**（React + Vite + TypeScript）— 端口 5173
- **后端 API**（Python + FastAPI）— 端口 8000

前端通过 Vite 代理 `/api` → `localhost:8000`。

## 开发命令

### 一键启动（Windows）
```bat
run.bat
```

### 单独启动

**后端：**
```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

**前端：**
```bash
cd frontend
npm install
npm run dev
```

**运行测试：**
```bash
cd backend
uv run pytest
uv run pytest tests/test_tools.py -v   # 单个文件
```

## 环境变量

根目录 `.env` 由后端 `config.py` 加载：

| 变量 | 用途 |
|------|------|
| `DASHSCOPE_API_KEY` | LLM API 密钥 |
| `OPENAI_BASE_URL` | API 地址（默认 DashScope） |
| `OPENAI_MODEL` | 对话模型（默认 `qwen3.5-plus`） |
| `TAVILY_API_KEY` | 联网搜索 API |
| `SYSTEM_PROMPT` | 系统提示词（可覆盖默认值） |

## 架构说明

### 请求流程
```
前端 useChat.ts → POST /api/chat → Agent Tool Use Loop → LLM
                                        ↓（按需调用）
                              search_web / read_file / run_python_code / search_knowledge
```

### 两条对话接口
- `POST /api/chat` — 普通文字对话
- `POST /api/chat/with-files` — 带文件/图片的对话（multipart/form-data）

### 后端关键文件
| 文件 | 作用 |
|------|------|
| `config.py` | 环境变量、模型白名单，单一事实来源 |
| `agent/core.py` | Tool Use Loop 核心，流式 generator |
| `api/chat.py` | 对话接口，管理 session、调用 Agent |
| `db.py` + `memory.py` | SQLite 会话持久化 |
| `rag/store.py` | ChromaDB 向量库存储与检索 |
| `rag/parser.py` | 文件解析（Word/Excel/PDF/CSV/TXT） |
| `vision.py` | 图片分析（qwen-vl-plus） |
| `tools/__init__.py` | 工具注册表（TOOLS_SCHEMA + TOOL_FUNCTIONS） |

### 前端关键文件
| 文件 | 作用 |
|------|------|
| `api/client.ts` | 所有后端请求封装 |
| `hooks/useChat.ts` | 对话状态、流式解析、AbortController |
| `components/QwenLayout/` | 主布局，入口组件 |
| `components/Chat/InputBox.tsx` | 输入框，支持文件附件 |
| `components/Sidebar/` | 历史会话列表 |
| `components/KnowledgePanel/` | 知识库管理面板 |

### 数据存储位置
- `data/chat.db` — SQLite 会话数据
- `data/chroma/` — ChromaDB 向量数据
- `data/` — 文件工具读写目录
