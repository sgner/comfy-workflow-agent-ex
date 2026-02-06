

// ComfyUI Workflow Data Structures

export interface ComfyNodeInput {
    name: string;
    type: string;
    link?: number | null;
}

export interface ComfyNodeOutput {
    name: string;
    type: string;
    links?: number[];
    slot_index?: number;
}

export interface ComfyNode {
    id: number;
    type: string;
    pos: [number, number];
    size: { 0: number; 1: number } | number[];
    flags: Record<string, any>;
    order: number;
    mode: number;
    inputs?: ComfyNodeInput[];
    outputs?: ComfyNodeOutput[];
    properties?: Record<string, any>;
    widgets_values?: any[];
    color?: string;
    bgcolor?: string;
}

// Changed from interface to tuple type for array destructuring support
export type ComfyLink = [number, number, number, number, number, string];

export interface ComfyWorkflow {
    id?: string;
    last_node_id: number;
    last_link_id: number;
    nodes: ComfyNode[];
    links: ComfyLink[];
    groups: any[];
    config: any;
    extra: any;
    version: number;
}

export interface WorkflowCheckpoint {
    id: string;
    timestamp: number;
    name: string;
    data: ComfyWorkflow;
}

// App Logic Types

export enum Sender {
    USER = 'user',
    AI = 'ai',
    SYSTEM = 'system'
}

export interface ChatMessage {
    id: string;
    sender: Sender;
    text: string;
    timestamp: Date;
    metadata?: {
        thinking?: boolean;
        workflowUpdate?: boolean;
        suggestedActions?: string[];
        missingNodes?: string[];
        groundingSources?: Array<{ uri: string; title: string }>;
        provider?: string; // To show which model generated this
        relatedQuestions?: string[];
    };
}

export interface AgentStatus {
    node: string;
    displayText: string;
    status: 'processing' | 'done' | 'error';
    details?: any;
}

export interface GeminiResponseSchema {
    chatResponse: string;
    updatedWorkflow?: ComfyWorkflow | null;
    missingNodes?: string[];
    suggestedActions?: string[];
    groundingSources?: Array<{ uri: string; title: string }>;
    issues?: WorkflowIssue[];
    relatedQuestions?: string[];
}

// Settings & Diagnostics

export type AIProvider = 'google' | 'custom';
export type Language = 'en' | 'zh' | 'ja' | 'ko';

export interface CustomConfig {
    endpoint?: string;
    headers?: string; // JSON string
    body?: string; // JSON string
}

export interface AppSettings {
    provider: AIProvider;
    apiKey: string; // For Google or Custom (if needed)
    modelName: string; // e.g., "gemini-2.5-flash" or "llama3"
    baseUrl?: string; // For custom/local (e.g., "http://localhost:11434/v1")
    language: Language;
    customConfig?: CustomConfig;
    activeBackendConfigId?: string;
    // Python Backend Settings
    usePythonBackend: boolean;
    pythonBackendUrl: string;
}

export type IssueSeverity = 'error' | 'warning' | 'info';

export interface WorkflowIssue {
    id: string;
    nodeId: number | null;
    severity: IssueSeverity;
    message: string;
    fixSuggestion?: string;
}

export type VisualizerTab = 'preview' | 'analysis' | 'json';

// Backend Configuration Types

export interface BackendConfig {
    id: string;
    provider: string; // 'google' | 'openai' | 'anthropic' | 'custom'
    name: string;
    model_name?: string;
    base_url?: string;
    is_default: boolean;
    created_at: string;
    // Advanced Custom Config for Backend
    custom_config?: CustomConfig;
}

export interface BackendConfigCreate {
    provider: string;
    name: string;
    api_key?: string;
    model_name?: string;
    base_url?: string;
    is_default?: boolean;
    // Advanced Custom Config for Backend
    custom_config?: CustomConfig;
}

export interface GitHubTokenStatus {
    has_token: boolean;
    message?: string;
}