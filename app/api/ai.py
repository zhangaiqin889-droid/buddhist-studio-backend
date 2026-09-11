from fastapi import APIRouter
from pydantic import BaseModel

from app.providers.factory import get_ai_provider

router = APIRouter(prefix="/api/ai", tags=["ai"])


class ChatIn(BaseModel):
    messages: list[dict]
    context: str | None = None


@router.post("/chat")
async def chat(body: ChatIn):
    """AI老师对话入口（规范38/75条）。未配置 OpenAI Key 时如实返回未配置提示，不伪造回答。"""
    ai = get_ai_provider()
    reply = await ai.chat(body.messages, body.context)
    return {"reply": reply, "ai_configured": ai.is_configured}
