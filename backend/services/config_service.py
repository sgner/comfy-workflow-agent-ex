import json
import os
import uuid
from typing import List, Optional
from datetime import datetime
from backend.models import (
    APIProviderConfig,
    CreateProviderConfigRequest,
    UpdateProviderConfigRequest,
    DeleteProviderConfigResponse,
    GitHubTokenConfig,
    UpdateGitHubTokenRequest,
    GitHubTokenResponse,
    CustomConfig
)
from backend.config import settings
import logging

logger = logging.getLogger(__name__)


class ConfigService:
    def __init__(self):
        self.config_dir = os.path.join(settings.CHECKPOINT_DIR, "api_configs")
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_file = os.path.join(self.config_dir, "providers.json")
        self.github_token_file = os.path.join(self.config_dir, "github_token.json")
    
    def _load_configs(self) -> List[APIProviderConfig]:
        if not os.path.exists(self.config_file):
            logger.info(f"[Config] Config file not found: {self.config_file}")
            return []
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"[Config] Loaded {len(data)} configs from file")
                return [APIProviderConfig(**item) for item in data]
        except Exception as e:
            logger.error(f"[Config] Error loading configs: {e}", exc_info=True)
            return []
    
    def _save_configs(self, configs: List[APIProviderConfig]) -> None:
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump([config.model_dump() for config in configs], f, indent=2, ensure_ascii=False)
            logger.info(f"[Config] Saved {len(configs)} configs to file")
        except Exception as e:
            logger.error(f"[Config] Error saving configs: {e}", exc_info=True)
            raise Exception(f"Error saving configs: {e}")
    
    def create_config(self, request: CreateProviderConfigRequest) -> APIProviderConfig:
        configs = self._load_configs()
        
        config_id = str(uuid.uuid4())
        now = datetime.now().timestamp()
        
        logger.info(f"[Config] Creating new config: {request.name}, Provider: {request.provider.value}")
        
        if request.is_default:
            for config in configs:
                config.is_default = False
            logger.info(f"[Config] Setting {request.name} as default, clearing other defaults")
        
        custom_config_dict = None
        if request.provider.value == "custom" and request.custom_config:
            custom_config_dict = request.custom_config.model_dump()
            logger.info(f"[Config] Custom config provided: {custom_config_dict}")
        
        new_config = APIProviderConfig(
            id=config_id,
            provider=request.provider,
            name=request.name,
            api_key=request.api_key,
            model_name=request.model_name,
            base_url=request.base_url,
            is_default=request.is_default,
            custom_config=custom_config_dict,
            created_at=now,
            updated_at=now
        )
        
        configs.append(new_config)
        self._save_configs(configs)
        
        logger.info(f"[Config] Config created successfully: {config_id}")
        return new_config
    
    def get_configs(self) -> List[APIProviderConfig]:
        return self._load_configs()
    
    def get_config_by_id(self, config_id: str) -> Optional[APIProviderConfig]:
        configs = self._load_configs()
        for config in configs:
            if config.id == config_id:
                return config
        return None
    
    def get_default_config(self) -> Optional[APIProviderConfig]:
        configs = self._load_configs()
        for config in configs:
            if config.is_default:
                return config
        return None
    
    def get_config_by_provider(self, provider: str) -> Optional[APIProviderConfig]:
        configs = self._load_configs()
        for config in configs:
            if config.provider.value == provider:
                return config
        return None
    
    def update_config(self, config_id: str, request: UpdateProviderConfigRequest) -> Optional[APIProviderConfig]:
        configs = self._load_configs()
        
        logger.info(f"[Config] Updating config: {config_id}")
        
        for i, config in enumerate(configs):
            if config.id == config_id:
                updated_config = config.model_copy()
                
                if request.name is not None:
                    updated_config.name = request.name
                    logger.info(f"[Config] Updating name to: {request.name}")
                if request.api_key is not None:
                    updated_config.api_key = request.api_key
                    logger.info("[Config] Updating API key")
                if request.model_name is not None:
                    updated_config.model_name = request.model_name
                    logger.info(f"[Config] Updating model to: {request.model_name}")
                if request.base_url is not None:
                    updated_config.base_url = request.base_url
                    logger.info(f"[Config] Updating base URL to: {request.base_url}")
                
                if request.custom_config is not None:
                    if updated_config.provider.value == "custom":
                        updated_config.custom_config = request.custom_config.model_dump()
                        logger.info(f"[Config] Updating custom config")
                    else:
                        logger.warning(f"[Config] Cannot update custom_config for non-custom provider: {updated_config.provider.value}")
                
                if request.is_default is not None:
                    if request.is_default:
                        for c in configs:
                            c.is_default = False
                        logger.info(f"[Config] Setting {config_id} as default, clearing others")
                    updated_config.is_default = request.is_default
                
                updated_config.updated_at = datetime.now().timestamp()
                configs[i] = updated_config
                self._save_configs(configs)
                
                logger.info(f"[Config] Config updated successfully: {config_id}")
                return updated_config
        
        logger.warning(f"[Config] Config not found for update: {config_id}")
        return None
    
    def delete_config(self, config_id: str) -> DeleteProviderConfigResponse:
        configs = self._load_configs()
        
        logger.info(f"[Config] Deleting config: {config_id}")
        
        for i, config in enumerate(configs):
            if config.id == config_id:
                config_name = config.name
                configs.pop(i)
                self._save_configs(configs)
                logger.info(f"[Config] Config deleted successfully: {config_name} ({config_id})")
                return DeleteProviderConfigResponse(
                    success=True,
                    message="Config deleted successfully"
                )
        
        logger.warning(f"[Config] Config not found for deletion: {config_id}")
        return DeleteProviderConfigResponse(
            success=False,
            message="Config not found"
        )
    
    def set_default_config(self, config_id: str) -> Optional[APIProviderConfig]:
        configs = self._load_configs()
        
        logger.info(f"[Config] Setting default config: {config_id}")
        
        target_config = None
        for config in configs:
            if config.id == config_id:
                target_config = config
                break
        
        if target_config is None:
            logger.warning(f"[Config] Config not found for setting default: {config_id}")
            return None
        
        logger.info(f"[Config] Setting {target_config.name} ({config_id}) as default")
        for config in configs:
            config.is_default = False
        
        for i, config in enumerate(configs):
            if config.id == config_id:
                configs[i].is_default = True
                configs[i].updated_at = datetime.now().timestamp()
                break
        
        self._save_configs(configs)
        logger.info(f"[Config] Default config set successfully: {config_id}")
        return configs[i]

    def get_github_token(self) -> Optional[str]:
        if os.path.exists(self.github_token_file):
            try:
                with open(self.github_token_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("token")
            except Exception as e:
                print(f"Error loading GitHub token: {e}")
        return None

    def update_github_token(self, request: UpdateGitHubTokenRequest) -> GitHubTokenResponse:
        try:
            now = datetime.now().timestamp()
            token_config = GitHubTokenConfig(
                token=request.token,
                created_at=now,
                updated_at=now
            )
            
            with open(self.github_token_file, 'w', encoding='utf-8') as f:
                json.dump(token_config.model_dump(), f, indent=2, ensure_ascii=False)
            
            return GitHubTokenResponse(
                success=True,
                message="GitHub token updated successfully",
                has_token=True
            )
        except Exception as e:
            return GitHubTokenResponse(
                success=False,
                message=f"Error saving GitHub token: {e}",
                has_token=False
            )

    def delete_github_token(self) -> GitHubTokenResponse:
        try:
            if os.path.exists(self.github_token_file):
                os.remove(self.github_token_file)
            
            return GitHubTokenResponse(
                success=True,
                message="GitHub token deleted successfully",
                has_token=False
            )
        except Exception as e:
            return GitHubTokenResponse(
                success=False,
                message=f"Error deleting GitHub token: {e}",
                has_token=os.path.exists(self.github_token_file)
            )

    def has_github_token(self) -> bool:
        return os.path.exists(self.github_token_file)


config_service = ConfigService()