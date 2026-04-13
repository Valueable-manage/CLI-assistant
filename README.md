# CLI Assistant

**一个基于大语言模型的全功能个人 AI 助手**

多轮对话 · 联网搜索 · 代码执行 · 私有知识库 · 多 Agent 深度研究 · 语音交互

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.11x-009688?logo=fastapi)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent-orange)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 功能特性

| 功能 | 说明 |
|------|------|
| 💬 流式多轮对话 | 实时流式输出，支持随时中断，会话持久化 |
| 🔧 Tool Use Agent | 自动决策调用工具：联网搜索、文件读写、Python 代码执行、数据库查询 |
| 📚 RAG 知识库 | 上传 PDF/Word/Excel/CSV/TXT，混合检索（向量 + BM25 + RRF 融合算法） |
| 🖼️ 图片理解 | 上传图片调用视觉模型分析内容 |
| 🔬 多 Agent 深度研究 | Supervisor → 并行三路搜索 → Writer，自动生成结构化研究报告 |
| 🎙️ 语音交互 | 中文语音输入识别 + TTS 自动播报（Web Speech API） |
| 🧠 长期记忆 | 跨会话记忆用户偏好与背景信息 |
| 📊 可观测性 | LangSmith 全链路追踪（LLM + Tool + Agent 轮次） |
| 🏠 本地模型 | 支持 Ollama 本地部署（无需 API Key） |

---

## 技术栈

```
前端：React 18 + TypeScript + Vite
后端：Python 3.12 + FastAPI + LangGraph
LLM： 阿里云 DashScope（Qwen 系列）/ Ollama 本地模型
存储：SQLite（会话） + ChromaDB（向量库）
检索：BM25（jieba 分词） + 向量检索 + RRF 融合
追踪：LangSmith
```

---

## 快速开始

### 前置条件

- Python 3.12+（推荐使用 [uv](https://github.com/astral-sh/uv)）
- Node.js 18+

### 1. 克隆项目

```bash
git clone https://github.com/Valueable-manage/CLI-assistant.git
cd CLI-assistant
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填入你的 API Key：

```env
# 必填：阿里云 DashScope（https://dashscope.console.aliyun.com/）
DASHSCOPE_API_KEY=your_key_here

# 可选：Tavily 联网搜索（https://tavily.com/）
TAVILY_API_KEY=your_key_here

# 可选：LangSmith 追踪（https://smith.langchain.com/）
LANGSMITH_API_KEY=your_key_here
LANGSMITH_TRACING=true
```

### 3. 启动

**Windows 一键启动：**

```bat
run.bat
```

**手动启动：**

```bash
# 后端
cd backend && uv sync
uv run uvicorn app.main:app --reload --port 8000

# 前端（新终端）
cd frontend && npm install && npm run dev
```

访问 **http://localhost:5173**

---

## 项目结构

```
CLI-assistant/
├── backend/
│   └── app/
│       ├── agent/
│       │   ├── core.py          # LangGraph Agent（Tool Use 循环）
│       │   └── researcher.py    # Multi-Agent 深度研究
│       ├── api/
│       │   ├── chat.py          # 对话接口（普通 / 文件 / 研究）
│       │   └── knowledge.py     # 知识库管理
│       ├── rag/
│       │   ├── store.py         # 混合检索（BM25 + 向量 + RRF）
│       │   └── parser.py        # 文件解析
│       ├── tools/               # 工具集（搜索/文件/代码/数据库）
│       ├── config.py            # 模型与环境配置
│       ├── db.py                # SQLite 会话持久化
│       └── long_memory.py       # 跨会话长期记忆
├── frontend/
│   └── src/
│       ├── hooks/
│       │   ├── useChat.ts       # 对话状态与流式解析
│       │   └── useSpeech.ts     # 语音输入 / TTS
│       └── components/          # UI 组件
├── .env.example                 # 环境变量模板
└── run.bat                      # Windows 一键启动
```

---

## 使用指南

### 普通对话
直接输入消息，Agent 会自动决策是否调用工具（联网搜索、代码执行等）。

### 深度研究模式
点击工具栏 **🔍 普通模式** 切换为 **🔬 研究模式**，发送问题后启动多 Agent 流程，自动并行搜索并整合为带章节结构的研究报告。

### 知识库
右侧面板上传文档，之后可直接提问文档内容，系统通过混合检索找到最相关片段。

### 本地模型（Ollama）
```bash
ollama pull qwen2.5:7b
```
安装后在前端模型选择器切换即可，无需 API Key。

---

## 支持的模型

| 模型 | 类型 | 说明 |
|------|------|------|
| qwen3.5-plus | 云端 | 默认，能力最强 |
| qwen-turbo | 云端 | 快速低成本 |
| qwen2.5:7b | 本地 | 需安装 Ollama |

---

## License

[MIT](LICENSE)
