# CLI Assistant — 个人 AI 助手

> 基于大语言模型的全功能个人助手，支持多轮对话、工具调用、知识库检索、多 Agent 深度研究、语音交互等能力。

## 功能概览

| 功能 | 说明 |
|------|------|
| 流式对话 | 实时流式输出，支持随时中断 |
| Tool Use | 自动联网搜索、读写文件、执行 Python 代码、查询数据库 |
| RAG 知识库 | 上传 PDF/Word/Excel/CSV/TXT，混合检索（向量 + BM25 + RRF 融合） |
| 图片理解 | 上传图片，调用视觉模型（qwen-vl-plus）分析内容 |
| 多 Agent 深度研究 | Supervisor → 并行三路搜索 → Writer，生成结构化研究报告 |
| 语音输入 / TTS | 浏览器 Web Speech API，中文语音识别 + 自动播报 |
| 多会话管理 | 侧边栏历史列表，SQLite 持久化，对话导出 Markdown |
| 长期记忆 | 跨会话记忆用户信息与偏好 |
| 可观测性 | LangSmith 全链路追踪（LLM + Tool Use + Agent 轮次） |
| 本地模型 | 支持 Ollama 本地运行（qwen2.5:7b 等） |

---

## 技术栈

**后端**
- Python 3.12 + FastAPI + uvicorn
- LangGraph（Agent 状态图，Tool Use 循环 + Multi-Agent）
- OpenAI SDK（兼容 DashScope / Ollama 双端）
- ChromaDB（向量数据库）+ jieba（中文分词）
- LangSmith（可观测性追踪）
- SQLite（会话持久化）

**前端**
- React 18 + TypeScript + Vite
- Web Speech API（语音识别 / SpeechSynthesis TTS）
- SSE（Server-Sent Events）流式接收

---

## 快速开始

### 环境要求
- Python 3.12+
- Node.js 18+
- [uv](https://github.com/astral-sh/uv) 包管理器

### 1. 克隆项目

```bash
git clone https://github.com/<your-username>/CLI-assistant.git
cd CLI-assistant
```

### 2. 配置环境变量

在根目录创建 `.env` 文件：

```env
# 必填：阿里云 DashScope（注册：https://dashscope.console.aliyun.com/）
DASHSCOPE_API_KEY=your_dashscope_key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL=qwen3.5-plus

# 可选：Tavily 联网搜索（注册：https://tavily.com/）
TAVILY_API_KEY=your_tavily_key

# 可选：LangSmith 可观测性追踪（注册：https://smith.langchain.com/）
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=CLI-assistant

# 可选：自定义系统提示词
# SYSTEM_PROMPT=你是一个专业助手
```

### 3. 启动

**Windows 一键启动：**
```bat
run.bat
```

**手动分别启动：**
```bash
# 后端
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000

# 前端（新终端）
cd frontend
npm install
npm run dev
```

访问 **http://localhost:5173**

---

## 使用指南

### 普通对话
直接输入消息，助手会根据问题自动决策是否调用工具（搜索、代码执行等）。

### 深度研究模式
点击工具栏 **🔍 普通模式** 切换为 **🔬 研究模式**，发送问题后启动多 Agent 流程：
1. Supervisor 将问题拆解为 3 个搜索方向
2. 并行执行 3 路网络搜索
3. Writer 整合结果，生成带章节结构的研究报告

### 知识库
右侧知识库面板上传文档，之后直接提问文档内容，助手通过混合检索（语义 + 关键词）找到最相关片段回答。

### 语音功能
- **语音输入**：点击麦克风按钮开始，再次点击结束（需浏览器麦克风权限）
- **TTS 播报**：点击 **🔇 语音关** 开启后，AI 每次回复完成后自动朗读

### 本地模型（Ollama）
安装 Ollama 后拉取模型，在前端模型下拉框选择本地模型即可：
```bash
ollama pull qwen2.5:7b
```

---

## 项目结构

```
CLI-assistant/
├── backend/
│   └── app/
│       ├── agent/
│       │   ├── core.py          # LangGraph Agent 状态图（Tool Use 循环）
│       │   ├── researcher.py    # Multi-Agent 深度研究图
│       │   └── prompts.py       # 系统提示词
│       ├── api/
│       │   ├── chat.py          # 对话接口（普通 + 带文件 + 深度研究）
│       │   └── knowledge.py     # 知识库管理接口
│       ├── rag/
│       │   ├── store.py         # ChromaDB + 混合检索（BM25 + RRF）
│       │   ├── parser.py        # 文件解析（Word/Excel/PDF/CSV/TXT）
│       │   └── embedder.py      # 向量嵌入
│       ├── tools/
│       │   ├── search.py        # Tavily 网络搜索
│       │   ├── file_tool.py     # 文件读写
│       │   ├── run_code.py      # Python 代码沙箱执行
│       │   └── db_query.py      # SQLite 只读查询
│       ├── config.py            # 环境变量与模型白名单
│       ├── db.py                # 会话数据库（SQLite）
│       ├── memory.py            # 短期会话记忆
│       ├── long_memory.py       # 长期跨会话记忆
│       └── vision.py            # 图片分析（qwen-vl-plus）
├── frontend/
│   └── src/
│       ├── api/client.ts        # 后端请求封装（SSE 流式解析）
│       ├── hooks/
│       │   ├── useChat.ts       # 对话状态管理（流式 + 工具状态 + 中断）
│       │   └── useSpeech.ts     # 语音输入 / TTS
│       └── components/
│           ├── Chat/            # 消息列表、输入框、Prompt 模板
│           ├── QwenLayout/      # 主布局（含工具栏）
│           ├── Sidebar/         # 历史会话列表
│           └── KnowledgePanel/  # 知识库管理面板
├── .env                         # API Key 配置（不提交 Git）
├── run.bat                      # Windows 一键启动脚本
└── pyproject.toml
```

---

## 支持的模型

| 模型 ID | 类型 | 说明 |
|---------|------|------|
| `qwen3.5-plus-2026-02-15` | 云端 | 稳定版，推荐 |
| `qwen3.5-plus` | 云端 | 最新版 |
| `qwen-turbo` | 云端 | 快速低成本 |
| `qwen2.5:7b` | 本地（Ollama） | 需先安装 Ollama |

---

## 运行测试

```bash
cd backend
uv run pytest                           # 全部单元测试
uv run pytest tests/test_tools.py -v    # 工具模块测试
uv run python tests/eval_rag.py         # RAG 质量评估（需已上传知识库）
```

---

## License

MIT
