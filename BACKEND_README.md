# ComfyUI Workflow Agent Backend

后端服务使用 LangChain、LangGraph、FastMCP 和 FastAPI 构建。

## 功能特性

1. **错误诊断与解决方案搜索**
   - 自动搜索 GitHub Issues 和网络资源
   - 整合解决方案并提供修复建议
   - 支持自动修复（需要用户确认）

2. **工作流分析**
   - 解析 ComfyUI 工作流结构
   - 分析数据流和关键节点
   - 检测潜在问题和连接错误

3. **流式对话**
   - 支持 Server-Sent Events (SSE) 流式响应
   - 实时显示 AI 思考过程

4. **操作撤回**
   - 记录所有执行的操作
   - 支持一键撤回操作

5. **多 AI 提供商支持**
   - Google Gemini
   - OpenAI
   - Anthropic Claude
   - 自定义/本地模型

6. **API 配置管理**
   - 支持保存多个 API 提供商配置
   - 设置默认配置
   - 配置的增删改查
   - 自动从配置中读取 API 参数

7. **GitHub Token 管理**
   - 通过 API 接口配置 GitHub Token
   - 用于搜索 GitHub Issues 和解决方案
   - 支持更新和删除 Token
   - 优先从配置读取，其次从环境变量读取

## 安装依赖

```bash
pip install -r requirements.txt
```

## 环境变量配置

创建 `.env` 文件（可选，也可以通过 API 接口配置）：

```env
# Google API Key (推荐)
GOOGLE_API_KEY=your_google_api_key

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key

# Anthropic API Key
ANTHROPIC_API_KEY=your_anthropic_api_key

# GitHub Token (用于搜索 Issues，也可以通过 API 配置)
GITHUB_TOKEN=your_github_token

# 默认模型
DEFAULT_MODEL=gemini-2.0-flash-exp
DEFAULT_PROVIDER=google
```

**注意**：所有 API 密钥和 Token 都可以通过后端 API 接口进行配置，无需在环境变量中设置。

## 启动服务

### 方式一：直接启动

```bash
python -m backend.main
```

### 方式二：使用 uvicorn

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 方式三：作为 ComfyUI 扩展启动

在 ComfyUI 中加载此扩展时，后端服务会自动启动。

## API 端点

### 聊天接口

- `POST /api/chat/stream` - 流式对话
- `POST /api/chat/message` - 发送消息（非流式）

### 工作流接口

- `POST /api/workflow/parse` - 解析工作流
- `POST /api/workflow/analyze` - 分析工作流

### 操作接口

- `POST /api/actions/execute` - 执行操作
- `POST /api/actions/undo` - 撤回操作

### 配置管理接口

#### API 提供商配置

- `POST /api/configs` - 创建 API 配置
- `GET /api/configs` - 获取所有配置
- `GET /api/configs/{config_id}` - 获取单个配置
- `GET /api/configs/default` - 获取默认配置
- `PUT /api/configs/{config_id}` - 更新配置
- `DELETE /api/configs/{config_id}` - 删除配置
- `POST /api/configs/set-default` - 设置默认配置

#### GitHub Token 配置

- `GET /api/github-token` - 获取 GitHub Token 状态
- `PUT /api/github-token` - 更新 GitHub Token
- `DELETE /api/github-token` - 删除 GitHub Token

## API 文档

启动服务后访问：
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## FastMCP 工具

后端提供了 FastMCP 工具集，可以独立运行：

```bash
python -m backend.mcp.tools
```

可用的 MCP 工具：
- `search_github_issues` - 搜索 GitHub Issues
- `search_web` - 网络搜索
- `analyze_workflow` - 分析工作流
- `detect_workflow_issues` - 检测工作流问题
- `get_workflow_data_flow` - 获取数据流
- `execute_workflow_action` - 执行工作流操作
- `undo_workflow_action` - 撤回操作
- `get_action_history` - 获取操作历史
- `parse_error_log` - 解析错误日志
- `suggest_fixes` - 建议修复方案

## 项目结构

```
backend/
├── __init__.py
├── main.py              # FastAPI 主应用
├── config.py            # 配置管理
├── models.py            # Pydantic 数据模型
├── action_history.py    # 操作历史管理
├── agent/               # LangGraph Agent
│   ├── __init__.py
│   └── workflow_agent.py
├── routes/              # API 路由
│   ├── __init__.py
│   ├── chat.py
│   ├── workflow.py
│   ├── actions.py
│   └── config.py        # 配置管理路由
├── services/            # 业务逻辑
│   ├── __init__.py
│   ├── chat_service.py
│   ├── workflow_service.py
│   ├── action_service.py
│   └── config_service.py  # 配置管理服务
├── tools/               # 工具集
│   ├── __init__.py
│   ├── search_tools.py
│   ├── workflow_analyzer.py
│   └── action_tools.py
└── mcp/                 # FastMCP 工具
    ├── __init__.py
    └── tools.py
```

## 使用示例

### 流式对话请求

```python
import requests
import json

response = requests.post(
    "http://127.0.0.1:8000/api/chat/stream",
    json={
        "message": "我的工作流报错了，帮我看看",
        "error_log": "Error: Node 5 missing input",
        "workflow": {...},
        "session_id": "session-123",
        "language": "zh",
        "provider": "google"
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        data = json.loads(line.decode().replace("data: ", ""))
        print(data.get("chunk"), end="", flush=True)
```

### 工作流分析请求

```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/api/workflow/analyze",
    json={
        "workflow": {...},
        "session_id": "session-123",
        "language": "zh"
    }
)

print(response.json())
```

### 配置管理示例

#### 创建 API 配置

```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/api/configs",
    json={
        "provider": "google",
        "name": "My Google Gemini",
        "api_key": "your-google-api-key",
        "model_name": "gemini-2.5-flash",
        "is_default": True
    }
)

config = response.json()
print(f"Config ID: {config['id']}")
```

#### 获取所有配置

```python
response = requests.get("http://127.0.0.1:8000/api/configs")
data = response.json()

for config in data["configs"]:
    print(f"{config['name']} ({config['provider']}): {config['model_name']}")
```

#### 更新配置

```python
response = requests.put(
    "http://127.0.0.1:8000/api/configs/{config_id}",
    json={
        "model_name": "gemini-2.0-flash-exp",
        "api_key": "new-api-key"
    }
)
```

#### 设置默认配置

```python
response = requests.post(
    "http://127.0.0.1:8000/api/configs/set-default",
    json={"config_id": "config-uuid"}
)
```

#### 删除配置

```python
response = requests.delete(f"http://127.0.0.1:8000/api/configs/{config_id}")
print(response.json())
```

### 使用配置进行聊天

配置保存后，聊天时只需传递 `provider` 参数，后端会自动从配置中读取对应的 API key 和模型名称：

```python
import requests
import json

response = requests.post(
    "http://127.0.0.1:8000/api/chat/stream",
    json={
        "message": "我的工作流报错了，帮我看看",
        "session_id": "session-123",
        "language": "zh",
        "provider": "google"
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        data = json.loads(line.decode().replace("data: ", ""))
        print(data.get("chunk"), end="", flush=True)
```

### 配置优先级

Chat 服务会按以下优先级获取 API 参数：

1. 请求中直接传入的 `api_key`、`model_name`、`base_url`
2. 从保存的配置中读取（根据 provider 匹配）
3. 从环境变量中读取（`GOOGLE_API_KEY`、`OPENAI_API_KEY`、`ANTHROPIC_API_KEY`）
4. 使用默认模型名称

### GitHub Token 配置示例

#### 更新 GitHub Token

```python
import requests

response = requests.put(
    "http://127.0.0.1:8000/api/github-token",
    json={
        "token": "ghp_xxxxxxxxxxxxxxxxxxxx"
    }
)

result = response.json()
print(f"Success: {result['success']}, Message: {result['message']}")
```

#### 获取 GitHub Token 状态

```python
response = requests.get("http://127.0.0.1:8000/api/github-token")
status = response.json()

if status["has_token"]:
    print("GitHub Token 已配置")
else:
    print("GitHub Token 未配置")
```

#### 删除 GitHub Token

```python
response = requests.delete("http://127.0.0.1:8000/api/github-token")
result = response.json()

print(f"Success: {result['success']}, Message: {result['message']}")
```

#### GitHub Token 优先级

GitHub API 调用会按以下优先级获取 Token：

1. 从保存的配置中读取（通过 API 接口配置）
2. 从环境变量中读取（`GITHUB_TOKEN`）
3. 无 Token（匿名访问，可能受限）

## 前端集成

前端需要实现以下功能以配合后端：

1. **流式响应处理** - 使用 EventSource 或 fetch 处理 SSE 流
2. **操作确认** - 当 `requires_user_confirmation` 为 true 时，显示确认对话框
3. **操作撤回** - 提供 UI 按钮调用撤回接口
4. **工作流同步** - 接收后端返回的工作流修改并更新前端状态

## 许可证

MIT License
