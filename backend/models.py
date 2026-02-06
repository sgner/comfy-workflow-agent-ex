from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field,validator, field_validator
from enum import Enum


class Sender(str, Enum):
    USER = "user"
    AI = "ai"
    SYSTEM = "system"


class AIProvider(str, Enum):
    GOOGLE = "google"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"


class Language(str, Enum):
    EN = "en"
    ZH = "zh"
    JA = "ja"
    KO = "ko"


class ComfyNodeInput(BaseModel):
    name: str
    type: str
    link: Optional[int] = None


class ComfyNodeOutput(BaseModel):
    name: str
    type: str
    links: Optional[List[int]] = None
    slot_index: Optional[int] = None


class ComfyNode(BaseModel):
    id: int
    type: str
    pos: List[float]
    size: Union[Dict[str, Any], List[float]]
    flags: Dict[str, Any] = {}
    order: int
    mode: int
    inputs: Optional[List[ComfyNodeInput]] = None
    outputs: Optional[List[ComfyNodeOutput]] = None
    properties: Optional[Dict[str, Any]] = None
    widgets_values: Optional[List[Any]] = None
    color: Optional[str] = None
    bgcolor: Optional[str] = None


class ComfyLink(BaseModel):
    id: int
    origin_id: int
    origin_slot: int
    target_id: int
    target_slot: int
    type: str

    @classmethod
    def validate_array(cls, value):
        if isinstance(value, list) and len(value) >= 6:
            return cls(
                id=int(value[0]) if value[0] is not None else 0,
                origin_id=int(value[1]) if value[1] is not None else 0,
                origin_slot=int(value[2]) if value[2] is not None else 0,
                target_id=int(value[3]) if value[3] is not None else 0,
                target_slot=int(value[4]) if value[4] is not None else 0,
                type=str(value[5]) if value[5] is not None else ""
            )
        return value


class ComfyWorkflow(BaseModel):
    last_node_id: int
    last_link_id: int
    nodes: List[ComfyNode]
    links: List[Union[List[Any], ComfyLink]]
    groups: List[Any] = []
    config: Dict[str, Any] = {}
    extra: Dict[str, Any] = {}
    version: float = 0.2

    @validator('links', pre=True)
    def validate_links(cls, v):
        validated_links = []
        for link in v:
            if isinstance(link, list):
                if len(link) >= 6:
                    validated_links.append(ComfyLink(
                        id=link[0],
                        origin_id=link[1],
                        origin_slot=link[2],
                        target_id=link[3],
                        target_slot=link[4],
                        type=str(link[5])
                    ))
                else:
                    validated_links.append(link)
            elif isinstance(link, ComfyLink):
                validated_links.append(link)
            else:
                validated_links.append(link)
        return validated_links


class WorkflowIssue(BaseModel):
    id: str
    node_id: Optional[int] = None
    severity: str
    message: str
    fix_suggestion: Optional[str] = None


class WorkflowAnalysis(BaseModel):
    summary: str
    data_flow: List[str]
    key_nodes: List[Dict[str, Any]]
    issues: List[WorkflowIssue] = []
    suggestions: List[str] = []


class GroundingSource(BaseModel):
    uri: str
    title: str


class Solution(BaseModel):
    description: str
    steps: List[str]
    code_snippet: Optional[str] = None
    requires_action: bool = False
    action_type: Optional[str] = None


class ErrorSolution(BaseModel):
    error_type: str
    summary: str
    solutions: List[Solution]
    sources: List[GroundingSource]
    can_auto_fix: bool = False
    auto_fix_action: Optional[str] = None


class ChatMessage(BaseModel):
    id: str
    sender: Sender
    text: str
    timestamp: float
    metadata: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    message: str
    workflow: Optional[ComfyWorkflow] = None
    error_log: Optional[str] = None
    session_id: str
    config_id: str
    language: Language = Language.EN


class ChatChunk(BaseModel):
    chunk: str
    is_complete: bool = False
    metadata: Optional[Dict[str, Any]] = None


class ActionRequest(BaseModel):
    action_type: str
    action_data: Dict[str, Any] = {}
    session_id: str


class ActionResult(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    can_undo: bool = True
    undo_action: Optional[str] = None


class UndoRequest(BaseModel):
    session_id: str
    action_id: str


class UndoResult(BaseModel):
    success: bool
    message: str
    restored_state: Optional[Dict[str, Any]] = None


class WorkflowParseRequest(BaseModel):
    workflow: ComfyWorkflow
    session_id: str
    language: Language = Language.EN


class WorkflowParseResponse(BaseModel):
    analysis: WorkflowAnalysis
    workflow_json: Dict[str, Any]


class APIProviderConfig(BaseModel):
    id: str
    provider: AIProvider
    name: str
    api_key: str
    model_name: str
    base_url: Optional[str] = None
    is_default: bool = False
    custom_config: Optional[Dict[str, Any]] = None
    created_at: float
    updated_at: float


class CustomConfig(BaseModel):
    endpoint: Optional[str] = "/chat/completions"
    headers: Optional[str] = '{"Content-Type": "application/json", "Authorization": "Bearer $apiKey"}'
    body: Optional[str] = '{"model": "$model", "messages": $messages, "temperature": 0.5}'


class CreateProviderConfigRequest(BaseModel):
    provider: AIProvider
    name: str
    api_key: str
    model_name: str
    base_url: Optional[str] = None
    is_default: bool = False
    custom_config: Optional[CustomConfig] = None

    @field_validator('custom_config')
    @classmethod
    def validate_custom_config(cls, v, info):
        provider = info.data.get('provider')
        if provider == AIProvider.CUSTOM and v is None:
            raise ValueError('custom_config is required for custom provider')
        if provider is not None and provider != AIProvider.CUSTOM and v is not None:
            raise ValueError('custom_config is only allowed for custom provider')
        return v


class UpdateProviderConfigRequest(BaseModel):
    name: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    base_url: Optional[str] = None
    is_default: Optional[bool] = None
    custom_config: Optional[CustomConfig] = None


class ProviderConfigListResponse(BaseModel):
    configs: List[APIProviderConfig]
    total: int


class DeleteProviderConfigResponse(BaseModel):
    success: bool
    message: str


class SetDefaultProviderRequest(BaseModel):
    config_id: str


class GitHubTokenConfig(BaseModel):
    token: str
    created_at: float
    updated_at: float


class UpdateGitHubTokenRequest(BaseModel):
    token: str


class GitHubTokenResponse(BaseModel):
    success: bool
    message: str
    has_token: bool