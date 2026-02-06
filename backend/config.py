import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    
    DEFAULT_MODEL: str = "gemini-2.0-flash-exp"
    DEFAULT_PROVIDER: str = "google"
    
    GITHUB_TOKEN: Optional[str] = None
    
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 30
    
    ENABLE_STREAMING: bool = True
    
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CHECKPOINT_DIR: str = os.path.join(_BASE_DIR, "checkpoints")
    DATABASE_DIR: str = os.path.join(_BASE_DIR, "database")
    SQLITE_DB: str = os.path.join(DATABASE_DIR, "chat_history.db")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()


def get_github_token() -> Optional[str]:
    from backend.services.config_service import config_service
    
    token = config_service.get_github_token()
    if token:
        return token
    
    return settings.GITHUB_TOKEN


def ensure_directories():
    os.makedirs(settings.CHECKPOINT_DIR, exist_ok=True)
    os.makedirs(settings.DATABASE_DIR, exist_ok=True)
