# ComfyUI Workflow Agent

<div align="center">

![ComfyUI Workflow Agent](https://img.shields.io/badge/ComfyUI-Workflow%20Agent-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-red)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-purple)

**一个基于 LangGraph 的智能 ComfyUI 工作流助手**


<div align="center">

| 主界面 | 工作流分析 | API配置 |
|--------|----------|------------|
| ![主界面](https://github.com/sgner/images/blob/main/%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202026-02-06%20161412.png) | ![工作流分析](https://github.com/sgner/images/blob/main/%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202026-02-06%20161434.png) | ![API配置](https://github.com/sgner/images/blob/main/%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202026-02-06%20161533.png) |



</div>

</div>

---

## 中文

### 项目简介

ComfyUI Workflow Agent 是一个强大的 AI 驱动的工作流助手，专门为 ComfyUI 用户设计。它使用 LangGraph 进行对话编排，支持多个 AI 提供商，能够智能分析工作流、搜索解决方案、执行修复操作，并提供流式对话体验。

### 核心功能

#### 🤖 智能对话
- 基于 LangGraph 的对话编排系统
- 支持流式响应，实时显示 AI 回复
- 自动保存对话历史（基于 SQLite）
- 多语言支持（中文、英文、日文、韩文）

#### 🔍 智能搜索
- GitHub 问题搜索
- Web 知识库检索
- 自动分析解决方案
- 智能推荐修复方案

#### 📊 工作流分析
- 深入分析 ComfyUI 工作流结构
- 识别潜在问题和优化点
- 提供详细的改进建议

#### ⚡ 自动修复
- 自动执行修复操作
- 用户确认机制
- 操作历史记录

#### 🌐 多 AI 提供商支持
- **官方提供商**：Google (Gemini)、OpenAI (GPT)、Anthropic (Claude)
- **自定义 API**：支持任何兼容 OpenAI 格式的 API
- 灵活的配置管理
- 自动重试机制

### 技术栈

#### 后端
- **框架**：FastAPI 0.115+
- **AI 编排**：LangGraph 0.2+
- **LLM 集成**：LangChain 0.3+
- **数据库**：SQLite (用于对话历史)
- **HTTP 客户端**：httpx 0.28+
- **异步处理**：asyncio

#### 前端
- **框架**：React 18 + TypeScript
- **构建工具**：Vite
- **UI 库**：Tailwind CSS
- **国际化**：i18next
- **状态管理**：React Hooks

### 项目结构

```
comfy_workflow_agent/
├── backend/                    # 后端代码
│   ├── agent/                 # LangGraph 代理
│   │   └── workflow_agent.py  # 工作流代理实现
│   ├── routes/                # API 路由
│   │   ├── chat.py           # 对话接口
│   │   ├── config.py         # 配置管理
│   │   ├── actions.py        # 操作执行
│   │   └── workflow.py      # 工作流分析
│   ├── services/             # 业务逻辑
│   │   ├── chat_service.py   # 对话服务
│   │   ├── config_service.py # 配置服务
│   │   ├── action_service.py # 操作服务
│   │   └── workflow_service.py # 工作流服务
│   ├── tools/                # 工具函数
│   │   ├── search_tools.py   # 搜索工具
│   │   ├── action_tools.py   # 操作工具
│   │   └── workflow_analyzer.py # 工作流分析器
│   ├── models.py             # 数据模型
│   ├── config.py             # 配置文件
│   └── main.py              # FastAPI 应用入口
├── ui/                      # React 前端
│   ├── src/
│   │   ├── components/       # React 组件
│   │   ├── services/        # API 服务
│   │   └── utils/          # 工具函数
│   └── public/             # 静态资源
├── checkpoints/             # 检查点目录
│   └── api_configs/        # API 配置
├── database/               # SQLite 数据库
├── requirements.txt         # Python 依赖
├── start_backend.py        # 后端启动脚本
└── API_DOCUMENTATION.md   # API 文档
```

### 安装指南

#### 环境要求
- Python 3.8 或更高版本
- Node.js 16 或更高版本
- ComfyUI 环境

#### 后端安装

1. **克隆项目**
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/sgner/comfy-workflow-agent-ex
cd comfy_workflow_agent
```

2. **安装 Python 依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
cp .env.example .env
```

编辑 `.env` 文件，添加你的 API 密钥：
```env
GOOGLE_API_KEY=your-google-api-key
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
GITHUB_TOKEN=your-github-token
```

4. **可单独启动后端服务**
```bash
python start_backend.py
```

后端将在 `http://localhost:8000` 启动

#### 前端安装

1. **安装 Node.js 依赖**
```bash
cd ui
npm install
```

### 使用说明

#### 1. 配置 AI 提供商

访问 `http://localhost:8000/docs` 打开 API 文档，使用配置管理接口添加 AI 提供商：

**官方提供商示例（Google）**
```json
{
  "provider": "google",
  "name": "Google Gemini",
  "api_key": "your-google-api-key",
  "model_name": "gemini-2.0-flash-exp",
  "is_default": true
}
```

**自定义 API 示例**
```json
{
  "provider": "custom",
  "name": "Custom API",
  "api_key": "your-api-key",
  "model_name": "your-model-name",
  "base_url": "https://your-api.com",
  "custom_config": {
    "endpoint": "/v1/chat/completions",
    "headers": "{\"Content-Type\": \"application/json\", \"Authorization\": \"Bearer $apiKey\"}",
    "body": "{\"model\": \"$model\", \"messages\": $messages, \"temperature\": 0.5}"
  },
  "is_default": false
}
```

#### 2. 开始对话

使用流式对话接口：

```bash
curl -X POST "http://localhost:8000/api/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "帮我分析这个工作流",
    "session_id": "test-session",
    "config_id": "your-config-id",
    "language": "zh",
    "workflow": {
      "nodes": [],
      "links": []
    }
  }'
```

#### 3. 分析工作流

```bash
curl -X POST "http://localhost:8000/api/workflow/analyze" \
  -H "Content-Type": application/json" \
  -d '{
    "workflow": {
      "nodes": [
        {
          "id": 1,
          "type": "KSampler",
          "inputs": {...}
        }
      ],
      "links": [...]
    },
    "language": "zh"
  }'
```

### API 文档

详细的 API 文档请查看 [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

主要接口：
- `POST /api/chat/stream` - 流式对话
- `POST /api/chat/message` - 非流式对话
- `POST /api/workflow/analyze` - 工作流分析
- `GET /api/config/providers` - 获取提供商列表
- `POST /api/config/providers` - 创建提供商配置
- `PUT /api/config/providers/{id}` - 更新提供商配置
- `DELETE /api/config/providers/{id}` - 删除提供商配置

### 配置说明

#### 后端配置

在 `backend/config.py` 中配置：

```python
class Settings(BaseSettings):
    # API 密钥
    GOOGLE_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # 默认配置
    DEFAULT_MODEL: str = "gemini-2.0-flash-exp"
    DEFAULT_PROVIDER: str = "google"
    
    # 重试配置
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 30
    
    # 数据库配置
    CHECKPOINT_DIR: str = "checkpoints"
    DATABASE_DIR: str = "database"
    SQLITE_DB: str = "database/chat_history.db"
```

#### 前端配置

在 `ui/src/constants.ts` 中配置：

```typescript
export const API_BASE_URL = 'http://localhost:8000';
export const DEFAULT_LANGUAGE = 'zh';
```

### 功能特性详解

#### LangGraph 工作流编排

系统使用 LangGraph 进行对话编排，包含以下节点：

1. **classify_request** - 分析用户意图
2. **search_solutions** - 搜索解决方案
3. **analyze_workflow** - 分析工作流
4. **prepare_action** - 准备修复操作
5. **execute_action** - 执行修复操作
6. **generate_response** - 生成最终回复

#### 对话历史持久化

使用 SQLite 数据库保存对话历史，基于 LangGraph 的检查点机制：

- 自动保存每个会话的状态
- 支持多会话并发
- 断点续传功能

#### 错误处理和重试

- 自动重试机制（最多 3 次）
- 指数退避策略
- 详细的错误日志

#### 自定义 API 支持

支持任何兼容 OpenAI 格式的 API：

- 灵活的请求模板
- 自定义请求头
- 支持流式和非流式响应

### 开发指南

#### 添加新的 AI 提供商

1. 在 `backend/models.py` 中添加新的提供商类型
2. 在 `backend/agent/workflow_agent.py` 中添加对应的 LLM 初始化代码
3. 更新配置验证逻辑

#### 添加新的工具

1. 在 `backend/tools/` 中创建新的工具文件
2. 实现工具函数
3. 在 `workflow_agent.py` 中调用工具

#### 前端开发

```bash
cd ui
npm run dev      # 开发服务器
npm run build    # 生产构建
npm run preview  # 预览生产构建
```

### 常见问题

#### Q: 如何切换 AI 提供商？
A: 在对话请求中指定 `config_id` 参数，系统会自动使用对应的提供商配置。

#### Q: 对话历史保存在哪里？
A: 对话历史保存在 `database/chat_history.db` SQLite 数据库中。

#### Q: 如何添加自定义 API？
A: 使用配置管理接口创建自定义提供商配置，提供 `base_url`、`api_key` 和 `custom_config`。

#### Q: 支持哪些语言？
A: 目前支持中文、英文、日文、韩文。

### 贡献指南

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request


<div align="center">

**Made with ❤️ for ComfyUI Community**

</div>
