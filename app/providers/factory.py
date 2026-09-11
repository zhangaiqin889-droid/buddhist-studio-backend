"""
Provider 工厂：根据 .env 配置选择真实实现或本地占位实现。
业务代码只应该从这里拿 provider 实例，不要直接 import 具体供应商类（规范第99条）。
"""
from functools import lru_cache

from app.core.config import get_settings
from app.providers.base import AIProvider, STTProvider, TTSProvider, VectorProvider
from app.providers.local import LocalKeywordVectorProvider, NoopAIProvider, NoopSTTProvider, NoopTTSProvider

settings = get_settings()


@lru_cache
def get_ai_provider() -> AIProvider:
    if settings.AI_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        from app.providers.openai_provider import OpenAIProvider

        return OpenAIProvider()
    return NoopAIProvider()


@lru_cache
def get_stt_provider() -> STTProvider:
    if settings.AI_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        from app.providers.openai_provider import OpenAISTTProvider

        return OpenAISTTProvider()
    return NoopSTTProvider()


@lru_cache
def get_tts_provider() -> TTSProvider:
    if settings.AI_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        from app.providers.openai_provider import OpenAITTSProvider

        return OpenAITTSProvider()
    return NoopTTSProvider()


@lru_cache
def get_vector_provider() -> VectorProvider:
    return LocalKeywordVectorProvider()
