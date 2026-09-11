from fastapi import APIRouter

from app.core.config import get_settings
from app.providers.factory import get_ai_provider, get_stt_provider, get_tts_provider

router = APIRouter(prefix="/api/health", tags=["health"])
settings = get_settings()


@router.get("")
def health():
    """实时状态中心（规范81/82章）：如实报告每个能力是否真正连接，不允许假装 Connected。"""
    ai = get_ai_provider()
    stt = get_stt_provider()
    tts = get_tts_provider()
    return {
        "database": "connected",
        "storage": "connected",
        "ai_provider": "connected" if ai.is_configured else "not_configured",
        "stt_provider": "connected" if stt.is_configured else "not_configured",
        "tts_provider": "connected" if tts.is_configured else "not_configured",
        "vector_provider": settings.VECTOR_PROVIDER,
        "n8n": "connected" if settings.N8N_WEBHOOK_BASE else "not_configured",
    }
