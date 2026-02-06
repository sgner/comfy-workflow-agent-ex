from fastapi import APIRouter, HTTPException
from backend.models import (
    APIProviderConfig,
    CreateProviderConfigRequest,
    UpdateProviderConfigRequest,
    ProviderConfigListResponse,
    DeleteProviderConfigResponse,
    SetDefaultProviderRequest,
    UpdateGitHubTokenRequest,
    GitHubTokenResponse
)
from backend.services.config_service import config_service

router = APIRouter()


@router.post("/configs", response_model=APIProviderConfig)
async def create_config(request: CreateProviderConfigRequest):
    try:
        return config_service.create_config(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/configs", response_model=ProviderConfigListResponse)
async def list_configs():
    try:
        configs = config_service.get_configs()
        return ProviderConfigListResponse(configs=configs, total=len(configs))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/configs/{config_id}", response_model=APIProviderConfig)
async def get_config(config_id: str):
    config = config_service.get_config_by_id(config_id)
    if config is None:
        raise HTTPException(status_code=404, detail="Config not found")
    return config


@router.get("/configs/default", response_model=APIProviderConfig)
async def get_default_config():
    config = config_service.get_default_config()
    if config is None:
        raise HTTPException(status_code=404, detail="No default config found")
    return config


@router.put("/configs/{config_id}", response_model=APIProviderConfig)
async def update_config(config_id: str, request: UpdateProviderConfigRequest):
    config = config_service.update_config(config_id, request)
    if config is None:
        raise HTTPException(status_code=404, detail="Config not found")
    return config


@router.delete("/configs/{config_id}", response_model=DeleteProviderConfigResponse)
async def delete_config(config_id: str):
    result = config_service.delete_config(config_id)
    if not result.success:
        raise HTTPException(status_code=404, detail=result.message)
    return result


@router.post("/configs/set-default", response_model=APIProviderConfig)
async def set_default_config(request: SetDefaultProviderRequest):
    config = config_service.set_default_config(request.config_id)
    if config is None:
        raise HTTPException(status_code=404, detail="Config not found")
    return config


@router.get("/github-token", response_model=dict)
async def get_github_token_status():
    try:
        has_token = config_service.has_github_token()
        return {"has_token": has_token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/github-token", response_model=GitHubTokenResponse)
async def update_github_token(request: UpdateGitHubTokenRequest):
    try:
        return config_service.update_github_token(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/github-token", response_model=GitHubTokenResponse)
async def delete_github_token():
    try:
        return config_service.delete_github_token()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))