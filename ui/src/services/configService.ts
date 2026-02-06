
import { BackendConfig, BackendConfigCreate, GitHubTokenStatus } from '../types';

const getBaseUrl = (url: string) => url.replace(/\/$/, '');

// --- Provider Configuration Endpoints ---

export const fetchBackendConfigs = async (backendUrl: string): Promise<BackendConfig[]> => {
    const res = await fetch(`${getBaseUrl(backendUrl)}/api/configs`);
    if (!res.ok) throw new Error('Failed to fetch configs');
    const data = await res.json();
    return data.configs || [];
};

export const createBackendConfig = async (backendUrl: string, config: BackendConfigCreate): Promise<BackendConfig> => {
    if(config.provider !== 'custom'){
        delete config.custom_config
    }
    const res = await fetch(`${getBaseUrl(backendUrl)}/api/configs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
    });
    if (!res.ok) throw new Error('Failed to create config');
    return res.json();
};

export const updateBackendConfig = async (backendUrl: string, id: string, config: Partial<BackendConfigCreate>): Promise<BackendConfig> => {
    const res = await fetch(`${getBaseUrl(backendUrl)}/api/configs/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
    });
    if (!res.ok) throw new Error('Failed to update config');
    return res.json();
};

export const deleteBackendConfig = async (backendUrl: string, id: string): Promise<void> => {
    const res = await fetch(`${getBaseUrl(backendUrl)}/api/configs/${id}`, {
        method: 'DELETE'
    });
    if (!res.ok) throw new Error('Failed to delete config');
};

export const setBackendDefault = async (backendUrl: string, id: string): Promise<void> => {
    const res = await fetch(`${getBaseUrl(backendUrl)}/api/configs/set-default`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config_id: id })
    });
    if (!res.ok) throw new Error('Failed to set default config');
};

// --- GitHub Token Endpoints ---

export const getGitHubStatus = async (backendUrl: string): Promise<GitHubTokenStatus> => {
    try {
        const res = await fetch(`${getBaseUrl(backendUrl)}/api/github-token`);
        if (!res.ok) return { has_token: false };
        return res.json();
    } catch {
        return { has_token: false };
    }
};

export const updateGitHubToken = async (backendUrl: string, token: string): Promise<void> => {
    const res = await fetch(`${getBaseUrl(backendUrl)}/api/github-token`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token })
    });
    if (!res.ok) throw new Error('Failed to update GitHub token');
};

export const deleteGitHubToken = async (backendUrl: string): Promise<void> => {
    const res = await fetch(`${getBaseUrl(backendUrl)}/api/github-token`, {
        method: 'DELETE'
    });
    if (!res.ok) throw new Error('Failed to delete GitHub token');
};
