### Project Overview

ComfyUI Workflow Agent is an intelligent AI-powered workflow assistant designed specifically for ComfyUI users. It uses LangGraph for conversation orchestration, supports multiple AI providers, and can intelligently analyze workflows, search for solutions, execute repair operations, and provide streaming conversation experiences.

### Core Features

#### 🤖 Intelligent Chat
- LangGraph-based conversation orchestration system
- Streaming response support with real-time AI replies
- Automatic chat history persistence (SQLite-based)
- Multi-language support (Chinese, English, Japanese, Korean)

#### 🔍 Smart Search
- GitHub issue search
- Web knowledge base retrieval
- Automatic solution analysis
- Intelligent fix recommendations

#### 📊 Workflow Analysis
- In-depth analysis of ComfyUI workflow structure
- Identify potential issues and optimization points
- Provide detailed improvement suggestions

#### ⚡ Auto Fix
- Automatic execution of repair operations
- User confirmation mechanism
- Operation history tracking

#### 🌐 Multi AI Provider Support
- **Official Providers**: Google (Gemini), OpenAI (GPT), Anthropic (Claude)
- **Custom APIs**: Support any OpenAI-compatible API
- Flexible configuration management
- Automatic retry mechanism

### Tech Stack

#### Backend
- **Framework**: FastAPI 0.115+
- **AI Orchestration**: LangGraph 0.2+
- **LLM Integration**: LangChain 0.3+
- **Database**: SQLite (for chat history)
- **HTTP Client**: httpx 0.28+
- **Async Processing**: asyncio

#### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **UI Library**: Tailwind CSS
- **Internationalization**: i18next
- **State Management**: React Hooks

### Project Structure

```
comfy_workflow_agent/
├── backend/                    # Backend code
│   ├── agent/                 # LangGraph agent
│   │   └── workflow_agent.py  # Workflow agent implementation
│   ├── routes/                # API routes
│   │   ├── chat.py           # Chat endpoints
│   │   ├── config.py         # Configuration management
│   │   ├── actions.py        # Action execution
│   │   └── workflow.py      # Workflow analysis
│   ├── services/             # Business logic
│   │   ├── chat_service.py   # Chat service
│   │   ├── config_service.py # Configuration service
│   │   ├── action_service.py # Action service
│   │   └── workflow_service.py # Workflow service
│   ├── tools/                # Utility functions
│   │   ├── search_tools.py   # Search tools
│   │   ├── action_tools.py   # Action tools
│   │   └── workflow_analyzer.py # Workflow analyzer
│   ├── models.py             # Data models
│   ├── config.py             # Configuration
│   └── main.py              # FastAPI app entry
├── ui/                      # React frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── services/        # API services
│   │   └── utils/          # Utility functions
│   └── public/             # Static assets
├── checkpoints/             # Checkpoint directory
│   └── api_configs/        # API configurations
├── database/               # SQLite database
├── requirements.txt         # Python dependencies
├── start_backend.py        # Backend startup script
└── API_DOCUMENTATION.md   # API documentation
```

### Installation Guide

#### Requirements
- Python 3.8 or higher
- Node.js 16 or higher
- ComfyUI environment

#### Backend Installation

1. **Clone the project**
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/sgner/comfy-workflow-agent-ex
cd comfy_workflow_agent
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` file and add your API keys:
```env
GOOGLE_API_KEY=your-google-api-key
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
GITHUB_TOKEN=your-github-token
```

4. **Start backend server**
```bash
python start_backend.py
```

Backend will start at `http://localhost:8000`

#### Frontend Installation

1. **Install Node.js dependencies**
```bash
cd ui
npm install
```

2. **Start development server**
```bash
npm run dev
```

Frontend will start at `http://localhost:5173`

### Usage

#### 1. Configure AI Providers

Visit `http://localhost:8000/docs` to open API documentation and use configuration management to add AI providers:

**Official Provider Example (Google)**
```json
{
  "provider": "google",
  "name": "Google Gemini",
  "api_key": "your-google-api-key",
  "model_name": "gemini-2.0-flash-exp",
  "is_default": true
}
```

**Custom API Example**
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

#### 2. Start Chat

Use streaming chat endpoint:

```bash
curl -X POST "http://localhost:8000/api/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Help me analyze this workflow",
    "session_id": "test-session",
    "config_id": "your-config-id",
    "language": "en",
    "workflow": {
      "nodes": [],
      "links": []
    }
  }'
```

#### 3. Analyze Workflow

```bash
curl -X POST "http://localhost:8000/api/workflow/analyze" \
  -H "Content-Type: application/json" \
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
    "language": "en"
  }'
```

### API Documentation

For detailed API documentation, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

Main endpoints:
- `POST /api/chat/stream` - Streaming chat
- `POST /api/chat/message` - Non-streaming chat
- `POST /api/workflow/analyze` - Workflow analysis
- `GET /api/config/providers` - Get provider list
- `POST /api/config/providers` - Create provider configuration
- `PUT /api/config/providers/{id}` - Update provider configuration
- `DELETE /api/config/providers/{id}` - Delete provider configuration

### Configuration

#### Backend Configuration

Configure in `backend/config.py`:

```python
class Settings(BaseSettings):
    # API Keys
    GOOGLE_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Default Settings
    DEFAULT_MODEL: str = "gemini-2.0-flash-exp"
    DEFAULT_PROVIDER: str = "google"
    
    # Retry Configuration
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 30
    
    # Database Configuration
    CHECKPOINT_DIR: str = "checkpoints"
    DATABASE_DIR: str = "database"
    SQLITE_DB: str = "database/chat_history.db"
```

#### Frontend Configuration

Configure in `ui/src/constants.ts`:

```typescript
export const API_BASE_URL = 'http://localhost:8000';
export const DEFAULT_LANGUAGE = 'en';
```

### Feature Details

#### LangGraph Workflow Orchestration

The system uses LangGraph for conversation orchestration with the following nodes:

1. **classify_request** - Analyze user intent
2. **search_solutions** - Search for solutions
3. **analyze_workflow** - Analyze workflow
4. **prepare_action** - Prepare repair operations
5. **execute_action** - Execute repair operations
6. **generate_response** - Generate final response

#### Chat History Persistence

Uses SQLite database to save chat history based on LangGraph's checkpoint mechanism:

- Automatically saves state for each session
- Supports concurrent multi-session
- Resume from checkpoint functionality

#### Error Handling and Retry

- Automatic retry mechanism (up to 3 times)
- Exponential backoff strategy
- Detailed error logging

#### Custom API Support

Supports any OpenAI-compatible API:

- Flexible request templates
- Custom request headers
- Streaming and non-streaming response support

### Development Guide

#### Adding New AI Providers

1. Add new provider type in `backend/models.py`
2. Add corresponding LLM initialization code in `backend/agent/workflow_agent.py`
3. Update configuration validation logic

#### Adding New Tools

1. Create new tool file in `backend/tools/`
2. Implement tool functions
3. Call tools in `workflow_agent.py`

#### Frontend Development

```bash
cd ui
npm run dev      # Development server
npm run build    # Production build
npm run preview  # Preview production build
```

### FAQ

#### Q: How to switch AI providers?
A: Specify the `config_id` parameter in your chat request, and the system will automatically use the corresponding provider configuration.

#### Q: Where is chat history saved?
A: Chat history is saved in the `database/chat_history.db` SQLite database.

#### Q: How to add custom APIs?
A: Use the configuration management endpoint to create a custom provider configuration with `base_url`, `api_key`, and `custom_config`.

#### Q: Which languages are supported?
A: Currently supports Chinese, English, Japanese, and Korean.

### Contributing

Contributions are welcome! Please follow these steps:

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


---
