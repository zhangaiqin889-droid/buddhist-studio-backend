"""
佛学工作室后端统一配置。
硬性原则（V4规范 83条）：独立项目目录、独立配置、独立数据库、独立端口、独立日志、独立存储。
所有第三方供应商（OpenAI等）只通过环境变量注入，代码里绝不写死 API Key。
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- 独立端口（见 port.config.json，与前端 5793、n8n 5678、AI Video Studio 8765/8788 均不冲突）---
    APP_PORT: int = 5891
    APP_HOST: str = "0.0.0.0"

    # --- 独立存储/数据库/日志（不与其它项目共用路径）---
    DATABASE_URL: str = "sqlite:///./storage/buddhist_studio.db"
    STORAGE_ROOT: str = "./storage/resources"
    LOG_DIR: str = "./logs"

    # --- AI Provider 开关：未配置 Key 时系统仍可运行，只是 AI 相关能力返回 "not_configured" ---
    AI_PROVIDER: str = "none"  # none | openai
    OPENAI_API_KEY: str | None = None
    AI_REASONING_MODEL: str = "gpt-5"
    AI_FAST_MODEL: str = "gpt-5-mini"
    STT_MODEL: str = "whisper-1"
    TTS_MODEL: str = "tts-1"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # --- 向量层：默认本地关键词检索占位，可换 pgvector / OpenAI File Search ---
    VECTOR_PROVIDER: str = "local_keyword"

    # --- 上传限制 ---
    MAX_UPLOAD_MB: int = 200

    # --- n8n（可选）---
    N8N_WEBHOOK_BASE: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
