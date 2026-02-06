

import asyncio
import json
import logging
import os
import sqlite3
from typing import TypedDict, Annotated, List, Dict, Any, Optional, AsyncGenerator

import httpx
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.runnables import RunnableConfig
from langchain_core.callbacks.manager import adispatch_custom_event

from backend.models import APIProviderConfig
from backend.config import settings

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    config: APIProviderConfig
    workflow: Optional[Dict[str, Any]]
    error_log: Optional[str]
    session_id: str
    language: str
    provider: str
    api_key: Optional[str]
    model_name: Optional[str]
    base_url: Optional[str]
    current_step: str
    search_results: List[Dict[str, Any]]
    solutions: List[Dict[str, Any]]
    can_auto_fix: bool
    requires_user_confirmation: bool
    action_type: Optional[str]
    action_data: Optional[Dict[str, Any]]
    workflow_analysis: Optional[Dict[str, Any]]


class WorkflowAgent:
    # 定义节点描述，用于前端展示
    NODE_DESCRIPTIONS = {
        "classify_request": "正在分析您的意图...",
        "search_solutions": "正在检索知识库...",
        "analyze_workflow": "正在分析工作流结构...",
        "prepare_action": "正在规划解决方案...",
        "execute_action": "正在执行修复操作...",
        "generate_response": "正在生成回复..."
    }

    def __init__(self):
        self.workflow_graph = self._build_graph_structure()
        self.db_path = settings.SQLITE_DB
        self._ensure_db_dir()

    def _parse_template(self, template: str, variables: Dict[str, Any]) -> str:
        result = template
        for key, value in variables.items():
            placeholder = f"${key}"
            result = result.replace(placeholder, str(value))
        return result

    def _ensure_db_dir(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    def _build_graph_structure(self) -> StateGraph:
        """构建图结构，但不编译"""
        workflow = StateGraph(AgentState)

        workflow.add_node("classify_request", self._classify_request)
        workflow.add_node("search_solutions", self._search_solutions)
        workflow.add_node("analyze_workflow", self._analyze_workflow)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("prepare_action", self._prepare_action)
        workflow.add_node("execute_action", self._execute_action)

        workflow.set_entry_point("classify_request")

        workflow.add_conditional_edges(
            "classify_request",
            self._route_after_classification,
            {
                "search": "search_solutions",
                "analyze": "analyze_workflow",
                "respond": "generate_response"
            }
        )

        workflow.add_conditional_edges(
            "search_solutions",
            self._route_after_search,
            {
                "prepare_action": "prepare_action",
                "respond": "generate_response"
            }
        )

        workflow.add_conditional_edges(
            "analyze_workflow",
            self._route_after_analysis,
            {
                "prepare_action": "prepare_action",
                "respond": "generate_response"
            }
        )

        workflow.add_conditional_edges(
            "prepare_action",
            self._route_after_prepare,
            {
                "execute": "execute_action",
                "respond": "generate_response"
            }
        )

        workflow.add_edge("execute_action", "generate_response")
        workflow.add_edge("generate_response", END)

        return workflow

    async def _classify_request(self, state: AgentState):
        from langchain_openai import ChatOpenAI
        from backend.config import settings

        messages = state["messages"]
        last_message = messages[-1] if messages else None

        if not last_message:
            state["current_step"] = "respond"
            return state

        prompt = f"""
        Analyze the user's request and classify it into one of these categories:
        1. "search" - User is reporting an error or asking for help with a problem
        2. "analyze" - User wants to understand or analyze a workflow
        3. "respond" - General conversation or other requests
        
        User Request: "{last_message.content}"
        
        Error log present: {bool(state.get("error_log"))}
        Workflow present: {bool(state.get("workflow"))}
        
        Respond with only the category name.
        """

        try:
            llm = None
            if state["provider"] == "custom":
                response = ""
                async for chunk in self._call_custom_api(state["config"], [HumanMessage(content=prompt)], None, stream=True):
                    response += chunk
                category = response.strip().lower()
                logger.info(f"[Custom API] Classification result: {category}")
                if category in ["search", "analyze", "respond"]:
                    return {"current_step": category}
                else:
                    return {"current_step": "respond"}

            if state["provider"] == "google":
                from langchain_google_genai import ChatGoogleGenerativeAI
                llm = ChatGoogleGenerativeAI(
                    model=state.get("model_name", settings.DEFAULT_MODEL),
                    api_key=state.get("api_key") or settings.GOOGLE_API_KEY
                )
            elif state["provider"] == "openai":
                llm = ChatOpenAI(
                    model=state.get("model_name", "gpt-4o"),
                    api_key=state.get("api_key") or settings.OPENAI_API_KEY
                )
            elif state["provider"] == "anthropic":
                from langchain_anthropic import ChatAnthropic
                llm = ChatAnthropic(
                    model=state.get("model_name", "claude-3-5-sonnet-20241022"),
                    api_key=state.get("api_key") or settings.ANTHROPIC_API_KEY
                )
            response = await llm.ainvoke([HumanMessage(content=prompt)])
            category = response.content.strip().lower()

            if category in ["search", "analyze", "respond"]:
                return {"current_step": category}
            else:
                return {"current_step": "respond"}
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return {"current_step": "respond"}

    async def _search_solutions(self, state: AgentState) -> AgentState:
        from backend.tools.search_tools import SearchTools

        search_tools = SearchTools()

        error_log = state.get("error_log", "")
        last_message = state["messages"][-1] if state["messages"] else None
        query = last_message.content if last_message else ""

        combined_query = f"{query} {error_log}".strip()

        search_results = await search_tools.search_github(combined_query)
        web_results = await search_tools.search_web(combined_query)

        state["search_results"] = search_results + web_results

        if search_results or web_results:
            state["solutions"] = await search_tools.analyze_solutions(
                state["search_results"],
                error_log,
                state["language"]
            )

        state["can_auto_fix"] = any(
            sol.get("requires_action", False)
            for sol in state.get("solutions", [])
        )

        return state

    async def _analyze_workflow(self, state: AgentState) -> AgentState:
        from backend.tools.workflow_analyzer import WorkflowAnalyzer
        from langchain_openai import ChatOpenAI
        from backend.config import settings

        analyzer = WorkflowAnalyzer()
        workflow = state.get("workflow")

        if workflow:
            # Construct LLM Call Function
            async def llm_call_wrapper(prompt: str) -> str:
                try:
                    if state["provider"] == "custom":
                        response = ""
                        async for chunk in self._call_custom_api(state["config"], [HumanMessage(content=prompt)], None, stream=True):
                            response += chunk
                        return response
                    
                    llm = None
                    if state["provider"] == "google":
                        from langchain_google_genai import ChatGoogleGenerativeAI
                        llm = ChatGoogleGenerativeAI(
                            model=state.get("model_name", settings.DEFAULT_MODEL),
                            api_key=state.get("api_key") or settings.GOOGLE_API_KEY
                        )
                    elif state["provider"] == "openai":
                        llm = ChatOpenAI(
                            model=state.get("model_name", "gpt-4o"),
                            api_key=state.get("api_key") or settings.OPENAI_API_KEY
                        )
                    elif state["provider"] == "anthropic":
                        from langchain_anthropic import ChatAnthropic
                        llm = ChatAnthropic(
                            model=state.get("model_name", "claude-3-5-sonnet-20241022"),
                            api_key=state.get("api_key") or settings.ANTHROPIC_API_KEY
                        )
                    
                    if llm:
                        res = await llm.ainvoke([HumanMessage(content=prompt)])
                        return res.content
                    return ""
                except Exception as e:
                    logger.error(f"Error in analysis LLM call: {e}")
                    return ""

            # Use LLM-based analysis
            analysis = await analyzer.analyze_workflow_with_llm(
                workflow, 
                llm_call_wrapper, 
                state["language"]
            )
            state["workflow_analysis"] = analysis

        return state

    async def _generate_response(self, state: AgentState,config: RunnableConfig):
        from langchain_openai import ChatOpenAI
        from backend.config import settings

        system_prompt = self._get_system_prompt(state)
        system_prompt += """
## CORE MISSION
1. **SOLVE ERRORS**: Identify, explain, and fix execution errors, missing connections, and incompatible types.
2. **EXPLAIN LOGIC**: Deconstruct complex workflows into clear, step-by-step explanations of how data flows (e.g., Load Image -> VAE Encode -> KSampler -> Decode).

## CAPABILITIES
1. **Analyze Workflows**: Understand the structure, data flow, and logic of the provided JSON.
2. **Modify Workflows**: Generate a VALID, COMPLETE JSON representation of the workflow when requested.
3. **Active Inquiry**: If a user's request is ambiguous, ASK for clarification.

## RESPONSE FORMAT
1. **For Explanations**: Use natural language with bold key terms. Break down the flow logically (e.g., "Step 1: Input", "Step 2: Processing").
2. **For Workflow Updates**:
   - Output the **FULL JSON** in a Markdown code block labeled \`json\`.
   - Example: \`\`\`json { ... } \`\`\`
   - **CRITICAL**: Ensure valid JSON. NO trailing commas. NO comments inside the JSON block.
3. **For Diagnostics / Issues**:
   - If you find specific problems, output them in a JSON array block labeled \`ISSUES_JSON\`.
   - Format: \`ISSUES_JSON: [{"nodeId": 10, "severity": "error", "message": "...", "fixSuggestion": "..."}]\`
4. **For Missing Nodes**:
   - Use a section: "SUGGESTED_ACTIONS: [Action1, Action2]".

## RULES
- **Always** validate connections.
- **Never** break JSON structure.
- When explaining, focus on **data flow** and **functionality**, not just node names.

## FINAL OUTPUT
At the end of your response, please provide 3 short "Related Questions" that user might want to ask next.
Format them as a JSON array labeled `RELATED_QUESTIONS`.
Example: `RELATED_QUESTIONS: ["Question 1?", "Question 2?"]`
`;
        """
        
        # Limit history to last 10 messages
        all_messages = state["messages"]
        # Ensure we always include the last message (current user input)
        recent_messages = all_messages[-10:] if len(all_messages) > 10 else all_messages
        
        try:
            llm = None
            if state["provider"] == "custom":
                full_content = ""
                async for chunk in self._call_custom_api(state["config"], recent_messages, system_prompt, stream=True):
                    await adispatch_custom_event(
                        "custom_chunk",
                        {"chunk": chunk},
                        config=config
                    )
                    full_content += chunk
                logger.info(f"Response: {full_content}")
                
                response = AIMessage(content=full_content)
                return {"messages": [response]}

            if state["provider"] == "google":
                from langchain_google_genai import ChatGoogleGenerativeAI
                llm = ChatGoogleGenerativeAI(
                    model=state.get("model_name", settings.DEFAULT_MODEL),
                    api_key=state.get("api_key") or settings.GOOGLE_API_KEY
                )
            elif state["provider"] == "openai":
                llm = ChatOpenAI(
                    model=state.get("model_name", "gpt-4o"),
                    api_key=state.get("api_key") or settings.OPENAI_API_KEY
                )
            elif state["provider"] == "anthropic":
                from langchain_anthropic import ChatAnthropic
                llm = ChatAnthropic(
                    model=state.get("model_name", "claude-3-5-sonnet-20241022"),
                    api_key=state.get("api_key") or settings.ANTHROPIC_API_KEY
                )

            # Construct messages with System Prompt + Recent History
            messages = [SystemMessage(content=system_prompt)] + recent_messages

            response = await llm.ainvoke(messages, config=config)

            return {"messages": [response]}
        except Exception as e:
            return {"messages": [AIMessage(content=f"Error generating response: {str(e)}")]}

    async def _prepare_action(self, state: AgentState) -> AgentState:
        solutions = state.get("solutions", [])

        if solutions:
            actionable_solution = next(
                (sol for sol in solutions if sol.get("requires_action", False)),
                None
            )

            if actionable_solution:
                state["requires_user_confirmation"] = True
                state["action_type"] = actionable_solution.get("action_type")
                state["action_data"] = actionable_solution.get("action_data", {})

        return state

    async def _execute_action(self, state: AgentState) -> AgentState:
        from backend.tools.action_tools import ActionTools

        action_tools = ActionTools()

        if state.get("action_type") and state.get("action_data"):
            result = await action_tools.execute_action(
                state["action_type"],
                state["action_data"],
                state["session_id"]
            )
            state["action_data"]["result"] = result

        return state

    def _route_after_classification(self, state: AgentState) -> str:
        return state.get("current_step", "respond")

    def _route_after_search(self, state: AgentState) -> str:
        if state.get("can_auto_fix", False):
            return "prepare_action"
        return "respond"

    def _route_after_analysis(self, state: AgentState) -> str:
        return "respond"

    def _route_after_prepare(self, state: AgentState) -> str:
        if state.get("requires_user_confirmation", False):
            return "respond"
        return "execute"

    def _get_system_prompt(self, state: AgentState) -> str:
        language = state.get("language", "en")

        language_map = {
            "en": "You are ComfyUI Workflow Agent, an expert assistant specialized in ComfyUI workflows.",
            "zh": "你是 ComfyUI 工作流助手，专门帮助用户解决 ComfyUI 工作流问题。",
            "ja": "あなたは ComfyUI ワークフローエージェントです。",
            "ko": "당신은 ComfyUI 워크플로우 에이전트입니다."
        }

        base_prompt = language_map.get(language, language_map["en"])

        if state.get("search_results"):
            base_prompt += f"\n\nSearch Results:\n{state['search_results']}"

        if state.get("solutions"):
            base_prompt += f"\n\nSolutions:\n{state['solutions']}"

        if state.get("workflow_analysis"):
            base_prompt += f"\n\nWorkflow Analysis:\n{state['workflow_analysis']}"

        if state.get("requires_user_confirmation"):
            base_prompt += "\n\nIMPORTANT: Ask the user if they want to execute the suggested action."

        return base_prompt

    async def _call_custom_api(self, config: APIProviderConfig, messages: List[Any], system_prompt,stream: bool = False,
                               max_retries: int = 3, retry_delay: float = 2.0) -> AsyncGenerator[str, None]:
        if not config.custom_config:
            raise ValueError("Custom config is required for custom provider")

        custom_config = config.custom_config
        endpoint = custom_config.get("endpoint", "/v1/chat/completions")
        headers_template = custom_config.get("headers",
                                             '{"Content-Type": "application/json", "Authorization": "Bearer $apiKey"}')
        body_template = custom_config.get("body", '{"model": "$model", "messages": $messages, "temperature": 0.5}')

        logger.info(f"[Custom API] Calling custom API with config: {config.name}")
        logger.info(f"[Custom API] Base URL: {config.base_url}")
        logger.info(f"[Custom API] Endpoint: {endpoint}")
        logger.info(f"[Custom API] Model: {config.model_name}")
        logger.info(f"[Custom API] Stream: {stream}")

        messages_list = []
        if system_prompt:
            messages_list.append({"role": "system", "content": system_prompt})
        for msg in messages:
            if isinstance(msg, dict):
                if msg.get("role") == "system" and system_prompt:
                    continue
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

                        req = client.build_request("POST", url, json=body, headers=headers)
                        async with client.stream(method="POST", url=url, json=body, headers=headers) as response:
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
                                line = line.strip()
                                if not line: continue

                                if line.startswith('data: '):
                                    data_str = line[6:]
                                    if data_str == '[DONE]':
                                        logger.info(f"[Custom API] Streaming completed.")
                                        break

                                    try:
                                        data = json.loads(data_str)
                                        # 兼容不同厂商的格式，这里主要适配 OpenAI 格式
                                        if 'choices' in data and len(data['choices']) > 0:
                                            delta = data['choices'][0].get('delta', {})
                                            content = delta.get('content', '')
                                            if content:
                                                full_text += content
                                                chunk_count += 1
                                                yield content
                                    except json.JSONDecodeError:
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


workflow_agent = WorkflowAgent()
