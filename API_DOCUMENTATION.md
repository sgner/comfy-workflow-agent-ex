# ComfyUI Workflow Agent Backend API Documentation

## Base URL

```
http://127.0.0.1:8000
```

## Overview

This API provides backend services for the ComfyUI Workflow Agent, including chat functionality, workflow analysis, action execution, and configuration management.

---

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible.

---

## API Endpoints

### 1. Chat Endpoints

#### 1.1 Stream Chat

Send a message and receive a streaming response from the AI agent. Chat history is automatically persisted using LangGraph's SQLite checkpoint system.

**Endpoint:** `POST /api/chat/stream`

**Request Body:**
```json
{
  "message": "string (required)",
  "workflow": {
    "last_node_id": 0,
    "last_link_id": 0,
    "nodes": [
      {
        "id": 0,
        "type": "string",
        "pos": [0.0, 0.0],
        "size": {"width": 0, "height": 0},
        "flags": {},
        "order": 0,
        "mode": 0,
        "inputs": [
          {
            "name": "string",
            "type": "string",
            "link": 0
          }
        ],
        "outputs": [
          {
            "name": "string",
            "type": "string",
            "links": [],
            "slot_index": 0
          }
        ],
        "properties": {},
        "widgets_values": [],
        "color": "string",
        "bgcolor": "string"
      }
    ],
    "links": [],
    "groups": [],
    "config": {},
    "extra": {},
    "version": 0.2
  },
  "error_log": "string (optional)",
  "session_id": "string (required)",
  "config_id": "string (required)",
  "language": "en|zh|ja|ko (default: en)"
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| message | string | Yes | The user's message |
| workflow | object | No | ComfyUI workflow JSON |
| error_log | string | No | Error log from ComfyUI |
| session_id | string | Yes | Unique session identifier for chat history persistence |
| config_id | string | Yes | Configuration ID from providers.json |
| language | string | No | Response language (en, zh, ja, ko) |

**Configuration Loading:**

- The API loads configuration from `checkpoints/api_configs/providers.json` using the `config_id`
- API key, model name, and base URL are automatically retrieved from the configuration
- Chat history is automatically persisted using LangGraph's SQLite checkpoint system

**Response:** Server-Sent Events (SSE) stream

**Response Format:**
```
data: {"chunk": "string", "is_complete": false, "metadata": {...}}

data: {"chunk": "", "is_complete": true, "metadata": {...}}
```

**Example:**
```bash
curl -X POST "http://127.0.0.1:8000/api/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain this workflow",
    "session_id": "test-session-123",
    "language": "en",
    "config_id": "869d2528-bba6-4b24-9736-2249929ebf8a"
  }'
```

---

#### 1.2 Send Message

Send a message and receive a non-streaming response. Chat history is automatically persisted using LangGraph's SQLite checkpoint system.

**Endpoint:** `POST /api/chat/message`

**Request Body:** Same as `/api/chat/stream`

**Response:**
```json
{
  "response": "string",
  "requires_user_confirmation": false,
  "action_type": "string (optional)",
  "action_data": {},
  "solutions": [],
  "search_results": []
}
```

**Example:**
```bash
curl -X POST "http://127.0.0.1:8000/api/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is this workflow doing?",
    "session_id": "test-session-123",
    "config_id": "869d2528-bba6-4b24-9736-2249929ebf8a"
  }'
```

---

### 2. Workflow Endpoints

#### 2.1 Parse Workflow

Parse and analyze a ComfyUI workflow.

**Endpoint:** `POST /api/workflow/parse`

**Request Body:**
```json
{
  "workflow": {
    "last_node_id": 0,
    "last_link_id": 0,
    "nodes": [],
    "links": [],
    "groups": [],
    "config": {},
    "extra": {},
    "version": 0.2
  },
  "session_id": "string (required)",
  "language": "en|zh|ja|ko (default: en)"
}
```

**Response:**
```json
{
  "analysis": {
    "summary": "string",
    "data_flow": ["string"],
    "key_nodes": [
      {
        "node_id": 0,
        "node_type": "string",
        "description": "string"
      }
    ],
    "issues": [
      {
        "id": "string",
        "node_id": 0,
        "severity": "error|warning|info",
        "message": "string",
        "fix_suggestion": "string"
      }
    ],
    "suggestions": ["string"]
  },
  "workflow_json": {}
}
```

**Example:**
```bash
curl -X POST "http://127.0.0.1:8000/api/workflow/parse" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow": {...},
    "session_id": "test-session-123",
    "language": "en"
  }'
```

---

#### 2.2 Analyze Workflow

Deep analyze a workflow for issues and optimization opportunities.

**Endpoint:** `POST /api/workflow/analyze`

**Request Body:** Same as `/api/workflow/parse`

**Response:** Same as `/api/workflow/parse`

**Example:**
```bash
curl -X POST "http://127.0.0.1:8000/api/workflow/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow": {...},
    "session_id": "test-session-123"
  }'
```

---

### 3. Action Endpoints

#### 3.1 Execute Action

Execute an action on the workflow.

**Endpoint:** `POST /api/actions/execute`

**Request Body:**
```json
{
  "action_type": "string (required)",
  "action_data": {},
  "session_id": "string (required)"
}
```

**Response:**
```json
{
  "success": true,
  "message": "string",
  "data": {},
  "can_undo": true,
  "undo_action": "string (optional)"
}
```

**Example:**
```bash
curl -X POST "http://127.0.0.1:8000/api/actions/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "add_node",
    "action_data": {"node_type": "KSampler"},
    "session_id": "test-session-123"
  }'
```

---

#### 3.2 Undo Action

Undo a previously executed action.

**Endpoint:** `POST /api/actions/undo`

**Request Body:**
```json
{
  "session_id": "string (required)",
  "action_id": "string (required)"
}
```

**Response:**
```json
{
  "success": true,
  "message": "string",
  "restored_state": {}
}
```

**Example:**
```bash
curl -X POST "http://127.0.0.1:8000/api/actions/undo" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-123",
    "action_id": "action-123"
  }'
```

---

### 4. Configuration Endpoints

#### 4.1 Create Configuration

Create a new AI provider configuration.

**Endpoint:** `POST /api/configs`

**Request Body:**
```json
{
  "provider": "google|openai|anthropic|custom (required)",
  "name": "string (required)",
  "api_key": "string (required)",
  "model_name": "string (required)",
  "base_url": "string (optional)",
  "is_default": false,
  "custom_config": {
    "endpoint": "/chat/completions (optional, default: /chat/completions)",
    "headers": "{\"Content-Type\": \"application/json\", \"Authorization\": \"Bearer $apiKey\"} (optional)",
    "body": "{\"model\": \"$model\", \"messages\": $messages, \"temperature\": 0.5} (optional)"
  }
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| provider | string | Yes | AI provider type (google, openai, anthropic, custom) |
| name | string | Yes | Configuration name |
| api_key | string | Yes | API key for the provider |
| model_name | string | Yes | Model name to use |
| base_url | string | No | Base URL (required for custom providers) |
| is_default | boolean | No | Set as default configuration |
| custom_config | object | No | Custom API configuration (required for custom providers, not allowed for others) |

**Important Notes:**

- **Custom Provider**: When `provider` is `custom`, `custom_config` is **required**
- **Official Providers**: When `provider` is `google`, `openai`, or `anthropic`, `custom_config` must be `null` or omitted
- **Validation Error**: The API will return an error if you try to set `custom_config` for non-custom providers

**Custom Config Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|----------|-------------|
| endpoint | string | /chat/completions | API endpoint path |
| headers | string | {"Content-Type": "application/json", "Authorization": "Bearer $apiKey"} | HTTP headers as JSON string with template variables |
| body | string | {"model": "$model", "messages": $messages, "temperature": 0.5} | Request body as JSON string with template variables |

**Template Variables:**

| Variable | Description |
|----------|-------------|
| $apiKey | API key from configuration |
| $model | Model name from configuration |
| $messages | Chat messages as JSON array |

**Response:**
```json
{
  "id": "string",
  "provider": "google",
  "name": "string",
  "api_key": "string",
  "model_name": "string",
  "base_url": "string (optional)",
  "is_default": false,
  "custom_config": {},
  "created_at": 0.0,
  "updated_at": 0.0
}
```

**Example (Google):**
```bash
curl -X POST "http://127.0.0.1:8000/api/configs" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "google",
    "name": "My Google Config",
    "api_key": "your-api-key",
    "model_name": "gemini-2.0-flash-exp",
    "is_default": true
  }'
```

**Example (Custom Provider with OpenAI-compatible API):**
```bash
curl -X POST "http://127.0.0.1:8000/api/configs" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "custom",
    "name": "Ollama Local",
    "api_key": "",
    "model_name": "llama2",
    "base_url": "http://localhost:11434",
    "custom_config": {
      "endpoint": "/v1/chat/completions",
      "headers": "{\"Content-Type\": \"application/json\"}",
      "body": "{\"model\": \"$model\", \"messages\": $messages, \"stream\": true}"
    }
  }'
```

**Example (Custom Provider with Custom Headers):**
```bash
curl -X POST "http://127.0.0.1:8000/api/configs" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "custom",
    "name": "Custom API",
    "api_key": "my-secret-key",
    "model_name": "gpt-4",
    "base_url": "https://api.example.com",
    "custom_config": {
      "endpoint": "/api/v1/chat",
      "headers": "{\"Content-Type\": \"application/json\", \"X-API-Key\": \"$apiKey\"}",
      "body": "{\"model\": \"$model\", \"messages\": $messages, \"temperature\": 0.7}"
    }
  }'
```

---

#### 4.2 List Configurations

Get all AI provider configurations.

**Endpoint:** `GET /api/configs`

**Response:**
```json
{
  "configs": [
    {
      "id": "string",
      "provider": "google",
      "name": "string",
      "api_key": "string",
      "model_name": "string",
      "base_url": "string (optional)",
      "is_default": false,
      "custom_config": {},
      "created_at": 0.0,
      "updated_at": 0.0
    }
  ],
  "total": 0
}
```

**Example:**
```bash
curl -X GET "http://127.0.0.1:8000/api/configs"
```

---

#### 4.3 Get Configuration by ID

Get a specific configuration by ID.

**Endpoint:** `GET /api/configs/{config_id}`

**Path Parameters:**
- `config_id` (string, required): Configuration ID

**Response:**
```json
{
  "id": "string",
  "provider": "google",
  "name": "string",
  "api_key": "string",
  "model_name": "string",
  "base_url": "string (optional)",
  "is_default": false,
  "created_at": 0.0,
  "updated_at": 0.0
}
```

**Example:**
```bash
curl -X GET "http://127.0.0.1:8000/api/configs/550e8400-e29b-41d4-a716-446655440000"
```

---

#### 4.4 Get Default Configuration

Get the default configuration.

**Endpoint:** `GET /api/configs/default`

**Response:** Same as `/api/configs/{config_id}`

**Example:**
```bash
curl -X GET "http://127.0.0.1:8000/api/configs/default"
```

---

#### 4.5 Update Configuration

Update an existing configuration.

**Endpoint:** `PUT /api/configs/{config_id}`

**Path Parameters:**
- `config_id` (string, required): Configuration ID

**Request Body:**
```json
{
  "name": "string (optional)",
  "api_key": "string (optional)",
  "model_name": "string (optional)",
  "base_url": "string (optional)",
  "is_default": false,
  "custom_config": {
    "endpoint": "/chat/completions (optional)",
    "headers": "{\"Content-Type\": \"application/json\", \"Authorization\": \"Bearer $apiKey\"} (optional)",
    "body": "{\"model\": \"$model\", \"messages\": $messages, \"temperature\": 0.5} (optional)"
  }
}
```

**Important Notes:**

- **Custom Provider**: When updating a custom provider, you can update `custom_config`
- **Official Providers**: Cannot update `custom_config` for google, openai, or anthropic providers
- **Validation Error**: The API will return an error if you try to update `custom_config` for non-custom providers

**Response:** Same as `/api/configs/{config_id}`

**Example:**
```bash
curl -X PUT "http://127.0.0.1:8000/api/configs/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "gemini-2.5-flash",
    "is_default": true
  }'
```

**Example (Update Custom Config):**
```bash
curl -X PUT "http://127.0.0.1:8000/api/configs/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "custom_config": {
      "endpoint": "/api/v2/chat",
      "body": "{\"model\": \"$model\", \"messages\": $messages, \"temperature\": 0.8}"
    }
  }'
```

---

#### 4.6 Delete Configuration

Delete a configuration.

**Endpoint:** `DELETE /api/configs/{config_id}`

**Path Parameters:**
- `config_id` (string, required): Configuration ID

**Response:**
```json
{
  "success": true,
  "message": "Config deleted successfully"
}
```

**Example:**
```bash
curl -X DELETE "http://127.0.0.1:8000/api/configs/550e8400-e29b-41d4-a716-446655440000"
```

---

#### 4.7 Set Default Configuration

Set a configuration as default.

**Endpoint:** `POST /api/configs/set-default`

**Request Body:**
```json
{
  "config_id": "string (required)"
}
```

**Response:** Same as `/api/configs/{config_id}`

**Example:**
```bash
curl -X POST "http://127.0.0.1:8000/api/configs/set-default" \
  -H "Content-Type: application/json" \
  -d '{
    "config_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

---

#### 4.8 Get GitHub Token Status

Check if GitHub token is configured.

**Endpoint:** `GET /api/github-token`

**Response:**
```json
{
  "has_token": true
}
```

**Example:**
```bash
curl -X GET "http://127.0.0.1:8000/api/github-token"
```

---

#### 4.9 Update GitHub Token

Update the GitHub token.

**Endpoint:** `PUT /api/github-token`

**Request Body:**
```json
{
  "token": "string (required)"
}
```

**Response:**
```json
{
  "success": true,
  "message": "GitHub token updated successfully",
  "has_token": true
}
```

**Example:**
```bash
curl -X PUT "http://127.0.0.1:8000/api/github-token" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "ghp_your_token_here"
  }'
```

---

#### 4.10 Delete GitHub Token

Delete the GitHub token.

**Endpoint:** `DELETE /api/github-token`

**Response:**
```json
{
  "success": true,
  "message": "GitHub token deleted successfully",
  "has_token": false
}
```

**Example:**
```bash
curl -X DELETE "http://127.0.0.1:8000/api/github-token"
```

---

### 5. System Endpoints

#### 5.1 Root

Get API information.

**Endpoint:** `GET /`

**Response:**
```json
{
  "message": "ComfyUI Workflow Agent API",
  "version": "1.0.0",
  "status": "running"
}
```

**Example:**
```bash
curl -X GET "http://127.0.0.1:8000/"
```

---

#### 5.2 Health Check

Check API health status.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy"
}
```

**Example:**
```bash
curl -X GET "http://127.0.0.1:8000/health"
```

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "detail": "Error message description"
}
```

**Common HTTP Status Codes:**

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request |
| 404 | Not Found |
| 500 | Internal Server Error |

---

## Configuration Selection Logic

When using chat endpoints, the API selects the AI provider configuration in the following priority order:

1. **Explicit Parameters**: If `api_key`, `model_name`, and/or `base_url` are provided in the request, they override all other configurations.

2. **Config ID**: If `config_id` is provided, the API loads the specific configuration by ID.

3. **Provider Match**: If no `config_id` is provided, the API finds the first configuration matching the `provider` type.

4. **Environment Variables**: If no configuration is found, the API falls back to environment variables:
   - `GOOGLE_API_KEY` for Google provider
   - `OPENAI_API_KEY` for OpenAI provider
   - `ANTHROPIC_API_KEY` for Anthropic provider

5. **Defaults**: If no environment variables are set, the API uses default settings from `config.py`.

---

## Custom API Provider

The API supports custom AI providers through the `custom_config` field in provider configurations. This allows you to integrate with any HTTP-based AI API.

### How Custom Providers Work

When you create a configuration with `provider: "custom"` and provide a `custom_config` object, the chat service will:

1. Use the `base_url` and `endpoint` from the custom config to construct the full API URL
2. Parse the `headers` template and replace variables (`$apiKey`, `$model`, `$messages`)
3. Parse the `body` template and replace variables
4. Send an HTTP POST request to the custom API
5. Handle streaming or non-streaming responses

### Template Variables

The following variables are available for use in `headers` and `body` templates:

| Variable | Description | Example |
|-----------|-------------|----------|
| `$apiKey` | The API key from the configuration | `Bearer $apiKey` |
| `$model` | The model name from the configuration | `"$model"` |
| `$messages` | Chat history as a JSON array string | `$messages` |

### Streaming Support

Custom providers support streaming responses. The API expects responses in OpenAI-compatible SSE format:

```
data: {"choices": [{"delta": {"content": "text chunk"}}]}
data: [DONE]
```

If your custom API uses a different streaming format, you may need to modify the `_call_custom_api` method in `chat_service.py`.

### Example Configurations

#### Ollama (Local LLM)

```json
{
  "provider": "custom",
  "name": "Ollama Local",
  "api_key": "",
  "model_name": "llama2",
  "base_url": "http://localhost:11434",
  "custom_config": {
    "endpoint": "/v1/chat/completions",
    "headers": "{\"Content-Type\": \"application/json\"}",
    "body": "{\"model\": \"$model\", \"messages\": $messages, \"stream\": true}"
  }
}
```

#### LM Studio (Local LLM)

```json
{
  "provider": "custom",
  "name": "LM Studio",
  "api_key": "",
  "model_name": "local-model",
  "base_url": "http://localhost:1234",
  "custom_config": {
    "endpoint": "/v1/chat/completions",
    "headers": "{\"Content-Type\": \"application/json\"}",
    "body": "{\"model\": \"$model\", \"messages\": $messages, \"temperature\": 0.7}"
  }
}
```

#### Custom API with Custom Authentication

```json
{
  "provider": "custom",
  "name": "My Custom API",
  "api_key": "my-secret-key",
  "model_name": "custom-model",
  "base_url": "https://api.example.com",
  "custom_config": {
    "endpoint": "/api/v1/chat",
    "headers": "{\"Content-Type\": \"application/json\", \"X-API-Key\": \"$apiKey\"}",
    "body": "{\"model\": \"$model\", \"messages\": $messages, \"temperature\": 0.5}"
  }
}
```

### Limitations

1. **Streaming Format**: Currently assumes OpenAI-compatible streaming format. Custom streaming formats may require code modifications.

2. **Error Handling**: Errors from custom APIs are returned as-is. You may need to parse error responses in your application.

3. **Request/Response Format**: The chat messages are converted to OpenAI format (`{"role": "user|assistant", "content": "..."}`). If your API requires a different format, you may need to modify the code.

4. **Timeout**: Default timeout is 60 seconds. This can be adjusted in the `_call_custom_api` method.

### Troubleshooting

**Issue**: "Invalid headers JSON" or "Invalid body JSON" error

**Solution**: Ensure your `headers` and `body` templates are valid JSON strings. Use double quotes for keys and values, and escape properly.

**Issue**: No response from custom API

**Solution**: Check that your `base_url` is correct and accessible. Ensure the `endpoint` path is correct (should start with `/`).

**Issue**: Streaming not working

**Solution**: Verify your custom API returns responses in OpenAI-compatible SSE format. If not, you may need to disable streaming or modify the parsing logic.

---

## Data Models

### AIProvider Enum

```typescript
"google" | "openai" | "anthropic" | "custom"
```

### Language Enum

```typescript
"en" | "zh" | "ja" | "ko"
```

### Sender Enum

```typescript
"user" | "ai" | "system"
```

### ComfyNode

```typescript
{
  id: number;
  type: string;
  pos: [number, number];
  size: { width: number; height: number };
  flags: Record<string, any>;
  order: number;
  mode: number;
  inputs?: Array<{
    name: string;
    type: string;
    link?: number;
  }>;
  outputs?: Array<{
    name: string;
    type: string;
    links?: number[];
    slot_index?: number;
  }>;
  properties?: Record<string, any>;
  widgets_values?: any[];
  color?: string;
  bgcolor?: string;
}
```

### ComfyWorkflow

```typescript
{
  last_node_id: number;
  last_link_id: number;
  nodes: ComfyNode[];
  links: any[];
  groups: any[];
  config: Record<string, any>;
  extra: Record<string, any>;
  version: number;
}
```

---

## Database and State Persistence

### SQLite Checkpoint System

The API uses LangGraph's SQLite checkpoint system to automatically persist chat history. This means:

- **Automatic History Persistence**: Chat messages are automatically saved to `database/chat_history.db`
- **Session-based Storage**: Each `session_id` maintains its own conversation history
- **No Manual History Required**: The `history` parameter has been removed from chat endpoints
- **State Recovery**: Previous conversations can be resumed by using the same `session_id`

### Database Location

```
database/chat_history.db
```

### Session Management

- Use a unique `session_id` for each conversation
- Reusing the same `session_id` will load previous chat history
- Chat history includes all messages exchanged in that session
- The checkpoint system handles both streaming and non-streaming requests

### Configuration File

Provider configurations are stored in:
```
checkpoints/api_configs/providers.json
```

Each configuration includes:
- `id`: Unique configuration identifier (used as `config_id`)
- `provider`: AI provider type (google, openai, anthropic, custom)
- `name`: Configuration name
- `api_key`: API key for the provider
- `model_name`: Model name to use
- `base_url`: Base URL (for custom providers)
- `custom_config`: Custom API configuration (for custom providers)

---

## Rate Limiting

Currently, there are no rate limits on the API endpoints.

---

## CORS

The API supports CORS (Cross-Origin Resource Sharing) and allows requests from any origin.

---

## WebSocket Support

Currently, the API does not support WebSocket connections. Use the SSE streaming endpoint for real-time responses.

---

## Version History

### v1.2.1
- Added validation for `custom_config` field
- `custom_config` is now **required** when `provider` is `custom`
- `custom_config` is **not allowed** when `provider` is `google`, `openai`, or `anthropic`
- Improved error messages for configuration validation

### v1.2.0
- Removed `provider`, `api_key`, `model_name`, `base_url`, `history` parameters from chat endpoints
- Made `config_id` a required parameter for chat endpoints
- Implemented LangGraph SQLite checkpoint system for automatic chat history persistence
- Configuration is now automatically loaded from `providers.json` using `config_id`
- Added database directory for SQLite checkpoint storage

### v1.1.0
- Added support for custom API providers
- Added `config_id` parameter to chat endpoints for precise configuration selection
- Added `custom_config` field to provider configurations
- Implemented template-based HTTP request customization for custom APIs
- Added support for streaming and non-streaming custom API calls

### v1.0.0
- Initial release
- Chat streaming and message endpoints
- Workflow parsing and analysis
- Action execution and undo
- Configuration management
- GitHub token integration

---

## Support

For issues or questions, please refer to the project repository or documentation.
