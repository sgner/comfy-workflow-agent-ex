

from typing import AsyncGenerator, Dict, Any, List, Optional
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from backend.models import ChatRequest, ChatChunk, APIProviderConfig
from backend.agent.workflow_agent import workflow_agent
from backend.config import settings
from backend.services.config_service import config_service
import json
import httpx
import re
import logging
import asyncio
from datetime import datetime
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self):
        self.agent = workflow_agent
        self.NODE_DESCRIPTIONS = {
            "classify_request": "正在分析您的意图...",
            "search_solutions": "正在检索知识库和 GitHub...",
            "analyze_workflow": "正在深入分析 ComfyUI 工作流结构...",
            "prepare_action": "正在规划修复方案...",
            "execute_action": "正在执行修复指令...",
            "generate_response": "正在整理最终回复..."
        }

    def _get_api_config(self, config_id: str) -> tuple[str, str, str, Optional[APIProviderConfig]]:
        config = config_service.get_config_by_id(config_id)

        logger.info(f"[Chat] Loading config by ID: {config_id}")

        if not config:
            logger.error(f"[Chat] Config not found: {config_id}")
            raise ValueError(f"Configuration not found: {config_id}")

        api_key = config.api_key
        model_name = config.model_name
        base_url = config.base_url

        logger.info(f"[Chat] Config loaded - Name: {config.name}, Provider: {config.provider.value}")
        logger.info(f"[Chat] Final config - Model: {model_name}, Base URL: {base_url}")

        return api_key, model_name, base_url, config

    def _parse_template(self, template: str, variables: Dict[str, Any]) -> str:
        result = template
        for key, value in variables.items():
            placeholder = f"${key}"
            result = result.replace(placeholder, str(value))
        return result

    async def _call_custom_api(self, config: APIProviderConfig, messages: List[Any], stream: bool = False,
                               max_retries: int = 3, retry_delay: float = 2.0) -> AsyncGenerator[str, None]:
        if not config.custom_config:
            raise ValueError("Custom config is required for custom provider")

        custom_config = config.custom_config
        endpoint = custom_config.get("endpoint", "/chat/completions")
        headers_template = custom_config.get("headers",
                                             '{"Content-Type": "application/json", "Authorization": "Bearer $apiKey"}')
        body_template = custom_config.get("body", '{"model": "$model", "messages": $messages, "temperature": 0.5}')

        logger.info(f"[Custom API] Calling custom API with config: {config.name}")
        logger.info(f"[Custom API] Base URL: {config.base_url}")
        logger.info(f"[Custom API] Endpoint: {endpoint}")
        logger.info(f"[Custom API] Model: {config.model_name}")
        logger.info(f"[Custom API] Stream: {stream}")

        messages_list = []
        for msg in messages:
            if isinstance(msg, dict):
                messages_list.append(msg)
            elif isinstance(msg, HumanMessage):
                messages_list.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                messages_list.append({"role": "assistant", "content": msg.content})

        logger.info(f"[Custom API] Final messages list: {json.dumps(messages_list, ensure_ascii=False)}")

        variables = {
            "apiKey": config.api_key or "",
            "model": config.model_name or "",
            "messages": json.dumps(messages_list)
        }

        url = f"{config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        logger.info(f"[Custom API] Full URL: {url}")

        headers_str = self._parse_template(headers_template, variables)
        try:
            headers = json.loads(headers_str)
        except json.JSONDecodeError:
            logger.error(f"[Custom API] Invalid headers JSON: {headers_str}")
            raise ValueError(f"Invalid headers JSON: {headers_str}")

        logger.info(f"[Custom API] Headers: {headers}")
        temp_template = body_template.replace('"$messages"', 'null').replace('$messages', 'null')
        variables_without_list = {k: v for k, v in variables.items() if k != 'messages'}
        body_str = self._parse_template(temp_template, variables_without_list)
        try:
            body = json.loads(body_str)
            body['messages'] = messages_list
        except json.JSONDecodeError:
            logger.error(f"[Custom API] Invalid body JSON: {body_str}")
            raise ValueError(f"Invalid body JSON: {body_str}")

        logger.info(f"[Custom API] Request body: {json.dumps(body, ensure_ascii=False)}")
        logger.info(
            f"[Custom API] Full request - URL: {url}, Headers: {headers}, Body: {json.dumps(body, ensure_ascii=False)}")

        retry_count = 0
        last_error = None

        while retry_count < max_retries:
            try:
                async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
                    if stream:
                        logger.info("[Custom API] Starting streaming request...")
                        response = await client.post(url, json=body, headers=headers)
                        logger.info(f"[Custom API] Response status: {response.status_code}")

                        if response.status_code >= 500:
                            raise httpx.HTTPStatusError(
                                f"Server error {response.status_code}",
                                request=None,
                                response=response
                            )

                        response.raise_for_status()

                        full_text = ""
                        chunk_count = 0
                        async for line in response.aiter_lines():
                            if line.strip().startswith('data: '):
                                data_str = line.strip()[6:]
                                if data_str == '[DONE]':
                                    logger.info(f"[Custom API] Streaming completed. Total chunks: {chunk_count}")
                                    break

                                try:
                                    data = json.loads(data_str)
                                    if 'choices' in data and len(data['choices']) > 0:
                                        delta = data['choices'][0].get('delta', {})
                                        content = delta.get('content', '')
                                        if content:
                                            full_text += content
                                            chunk_count += 1
                                            logger.debug(f"[Custom API] Chunk {chunk_count}: {content}")
                                            yield content
                                except json.JSONDecodeError as e:
                                    logger.warning(f"[Custom API] Failed to parse chunk: {e}")
                                    continue
                    else:
                        logger.info("[Custom API] Starting non-streaming request...")
                        response = await client.post(url, json=body, headers=headers)
                        logger.info(f"[Custom API] Response status: {response.status_code}")

                        if response.status_code >= 500:
                            raise httpx.HTTPStatusError(
                                f"Server error {response.status_code}",
                                request=None,
                                response=response
                            )

                        response.raise_for_status()

                        data = response.json()
                        logger.info(f"[Custom API] Response data: {json.dumps(data, ensure_ascii=False)}")

                        if 'choices' in data and len(data['choices']) > 0:
                            content = data['choices'][0].get('message', {}).get('content', '')
                            logger.info(f"[Custom API] Response content length: {len(content)}")
                            yield content
                        else:
                            logger.warning(f"[Custom API] Unexpected response format: {data}")
                            yield str(data)

                return

            except httpx.HTTPStatusError as e:
                last_error = e
                retry_count += 1

                if e.response and e.response.status_code >= 500 and retry_count <= max_retries:
                    logger.warning(
                        f"[Custom API] Server error {e.response.status_code}, retry {retry_count}/{max_retries} in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    logger.error(f"[Custom API] HTTP error: {e}")
                    raise

            except httpx.RequestError as e:
                last_error = e
                retry_count += 1

                if retry_count <= max_retries:
                    logger.warning(
                        f"[Custom API] Request error: {e}, retry {retry_count}/{max_retries} in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    logger.error(f"[Custom API] Request error: {e}")
                    raise

        logger.error(f"[Custom API] Max retries ({max_retries}) exceeded. Last error: {last_error}")
        raise last_error

    async def stream_chat(self, request: ChatRequest) -> StreamingResponse:
        agent_workflow = self.agent.workflow_graph
        async def generate():
            async with AsyncSqliteSaver.from_conn_string(self.agent.db_path) as checkpointer:
                try:
                    print(f"[Stream Chat] Starting stream chat for session: {request.session_id}")
                    print(f"[Stream Chat] Message: {request.message[:100]}...")
                    print(f"[Stream Chat] Config ID: {request.config_id}")

                    api_key, model_name, base_url, config = self._get_api_config(request.config_id)

                    logger.info(f"[Stream Chat] Using LangGraph agent with provider: {config.provider.value}")
                    state = {
                        "messages": [HumanMessage(content=request.message)],
                        "config": config,
                        "workflow": request.workflow.model_dump() if request.workflow else None,
                        "error_log": request.error_log,
                        "session_id": request.session_id,
                        "language": request.language.value,
                        "provider": config.provider.value,
                        "api_key": api_key,
                        "model_name": model_name,
                        "base_url": base_url,
                        "current_step": "",
                        "search_results": [],
                        "solutions": [],
                        "can_auto_fix": False,
                        "requires_user_confirmation": False,
                        "action_type": None,
                        "action_data": None,
                        "workflow_analysis": None
                    }

                    config_dict = {"configurable": {"thread_id": request.session_id}}
                    logger.info("[Stream Chat] Starting LangGraph agent stream...")
                    app = agent_workflow.compile(checkpointer=checkpointer)
                    async for event in app.astream_events(state, config_dict,version="v2"):
                        event_type = event["event"]
                        event_name = event["name"]
                        event_data = event["data"]

                        # ---------------------------------------------------------
                        # 场景 A: 捕获标准 LLM 的流式 Token (OpenAI, Google, Anthropic)
                        # ---------------------------------------------------------
                        if event_type == "on_chat_model_stream":
                            # data['chunk'] 是一个 AIMessageChunk 对象
                            chunk = event_data.get("chunk")
                            if chunk and chunk.content:
                                payload = {
                                    "chunk": chunk.content,
                                    "type": "content",  # 标记为内容
                                    "metadata": {"node": "generate_response"}
                                }
                                yield f"data: {json.dumps(payload)}\n\n"

                        # ---------------------------------------------------------
                        # 场景 B: 捕获 Custom API 的手动流事件
                        # ---------------------------------------------------------
                        elif event_type == "on_custom_event" and event_name == "custom_chunk":
                            # data 是你在 adispatch_custom_event 中传入的字典
                            content = event_data.get("chunk")
                            if content:
                                payload = {
                                    "chunk": content,
                                    "type": "content",
                                    "metadata": {"node": "generate_response"}
                                }
                                yield f"data: {json.dumps(payload)}\n\n"

                        # ---------------------------------------------------------
                        # 场景 C: 捕获节点切换状态 (UI显示“正在搜索...”)
                        # ---------------------------------------------------------
                        elif event_type == "on_chain_start":
                            # 过滤掉内部的小链，只关心图的主节点
                            if event_name in self.NODE_DESCRIPTIONS:
                                display_text = self.NODE_DESCRIPTIONS.get(event_name, "处理中...")
                                payload = {
                                    "chunk": "",
                                    "type": "status_update",
                                    "metadata": {
                                        "node": event_name,
                                        "display_text": display_text,
                                        "status": "processing"
                                    }
                                }
                                yield f"data: {json.dumps(payload)}\n\n"

                        # ---------------------------------------------------------
                        # 场景 D: 捕获特定节点的输出数据 (比如搜索结果)
                        # ---------------------------------------------------------
                        elif event_type == "on_chain_end":
                            if event_name == "search_solutions":
                                output = event_data.get("output", {})
                                # 如果 output 是 dict 且包含 search_results
                                if isinstance(output, dict) and "search_results" in output:
                                    results = output["search_results"]
                                    # 推送元数据给前端展示
                                    payload = {
                                        "chunk": "",
                                        "type": "meta_update",  # 元数据更新
                                        "metadata": {
                                            "node": event_name,
                                            "step_data": {
                                                "search_previews": [r.get("title") for r in results[:3]]
                                            }
                                        }
                                    }
                                    yield f"data: {json.dumps(payload)}\n\n"

                        # 3. 结束流
                    final_chunk = {
                        "chunk": "",
                        "is_complete": True,
                        "type": "end"
                    }
                    yield f"data: {json.dumps(final_chunk)}\n\n"
                    logger.info("[Stream Chat] Completed")

                except Exception as e:
                    logger.error(f"[Stream Chat] Error: {str(e)}", exc_info=True)
                    error_chunk = {
                        "chunk": f"Error: {str(e)}",
                        "is_complete": True,
                        "metadata": {"error": True}
                    }
                    yield f"data: {json.dumps(error_chunk)}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    async def process_message(self, request: ChatRequest) -> Dict[str, Any]:
        try:
            logger.info(f"[Process Message] Starting for session: {request.session_id}")
            logger.info(f"[Process Message] Message: {request.message[:100]}...")
            logger.info(f"[Process Message] Config ID: {request.config_id}")

            api_key, model_name, base_url, config = self._get_api_config(request.config_id)

            if config.provider.value == "custom" and config.custom_config:
                logger.info("[Process Message] Using custom API provider")
                messages_list = []
                messages_list.append({"role": "user", "content": request.message})

                response_text = ""
                async for chunk in self._call_custom_api(config, messages_list, stream=False):
                    response_text += chunk

                logger.info(f"[Process Message] Custom API response length: {len(response_text)}")
                return {
                    "response": response_text,
                    "requires_user_confirmation": False,
                    "action_type": None,
                    "action_data": None,
                    "solutions": [],
                    "search_results": []
                }

            logger.info(f"[Process Message] Using LangGraph agent with provider: {config.provider.value}")
            state = {
                "messages": [HumanMessage(content=request.message)],
                "workflow": request.workflow.model_dump() if request.workflow else None,
                "error_log": request.error_log,
                "session_id": request.session_id,
                "language": request.language.value,
                "provider": config.provider.value,
                "api_key": api_key,
                "model_name": model_name,
                "base_url": base_url,
                "current_step": "",
                "search_results": [],
                "solutions": [],
                "can_auto_fix": False,
                "requires_user_confirmation": False,
                "action_type": None,
                "action_data": None,
                "workflow_analysis": None
            }

            config_dict = {"configurable": {"thread_id": request.session_id}}
            
            # Use AsyncSqliteSaver to persist state, same as stream_chat
            async with AsyncSqliteSaver.from_conn_string(self.agent.db_path) as checkpointer:
                logger.info("[Process Message] Compiling and invoking agent...")
                app = self.agent.workflow_graph.compile(checkpointer=checkpointer)
                result = await app.ainvoke(state, config_dict)
                logger.info("[Process Message] Agent invoke completed")

                final_messages = result.get("messages", [])
                response_text = ""
                for msg in final_messages:
                    if isinstance(msg, AIMessage):
                        response_text += msg.content
                    elif hasattr(msg, "content") and hasattr(msg, "type") and msg.type == "ai":
                         # Handle case where messages might be dicts if not fully reconstituted
                         response_text += msg.content

                logger.info(f"[Process Message] Response length: {len(response_text)}")
                return {
                    "response": response_text,
                    "requires_user_confirmation": result.get("requires_user_confirmation", False),
                    "action_type": result.get("action_type"),
                    "action_data": result.get("action_data"),
                    "solutions": result.get("solutions", []),
                    "search_results": result.get("search_results", [])
                }

        except Exception as e:
            logger.error(f"[Process Message] Error: {str(e)}", exc_info=True)
            return {
                "response": f"Error processing message: {str(e)}",
                "error": True
            }

    async def get_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve chat history from LangGraph checkpointer"""
        try:
            config = {"configurable": {"thread_id": session_id}}
            async with AsyncSqliteSaver.from_conn_string(self.agent.db_path) as checkpointer:
                # Compile the graph with checkpointer to enable correct state hydration
                app = self.agent.workflow_graph.compile(checkpointer=checkpointer)
                
                # Use aget_state to retrieve the re-hydrated state object
                # This correctly deserializes messages back into LangChain objects
                state_snapshot = await app.aget_state(config)
                
                if not state_snapshot or not state_snapshot.values:
                    return []
                
                messages = state_snapshot.values.get("messages", [])
                
                # Format messages for frontend
                formatted_history = []
                # Only take the last 'limit' messages to avoid context overflow
                recent_messages = messages[-limit:] if limit > 0 else messages
                
                for msg in recent_messages:
                    msg_type = msg.type if hasattr(msg, "type") else "unknown"
                    content = msg.content if hasattr(msg, "content") else str(msg)
                    
                    if msg_type == "human":
                        formatted_history.append({
                            "sender": "user",
                            "text": content,
                            "timestamp": datetime.now().isoformat() 
                        })
                    elif msg_type == "ai":
                        formatted_history.append({
                            "sender": "ai",
                            "text": content,
                            "timestamp": datetime.now().isoformat()
                        })
                
                return formatted_history
        except Exception as e:
            logger.error(f"Error fetching history: {e}", exc_info=True)
            return []
