"""
OpenAI Provider 实现（规范第2/17/9/61条）。
仅在 settings.AI_PROVIDER == "openai" 且 OPENAI_API_KEY 已配置时才会被 factory 选中启用；
未配置时系统自动退回 app/providers/local.py 里的 Noop 实现，不会报错、也不会假装已连接。

TODO(用户提供 API Key 后生效): 目前请求体已按 OpenAI SDK 用法写好，
拿到 Key 后只需在 .env 设置 AI_PROVIDER=openai + OPENAI_API_KEY=sk-xxx 即可切换为真实调用，
代码不需要再改动（这正是 Provider 抽象的意义）。
"""
from app.core.config import get_settings
from app.providers.base import AIProvider, STTProvider, TTSProvider

settings = get_settings()


class OpenAIProvider(AIProvider):
    def __init__(self):
        self._client = None
        if settings.OPENAI_API_KEY:
            try:
                from openai import AsyncOpenAI  # 延迟导入：未安装/未配置时不报错

                self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            except ImportError:
                self._client = None

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    async def summarize(self, text: str) -> str | None:
        if not self.is_configured or not text:
            return None
        resp = await self._client.chat.completions.create(
            model=settings.AI_FAST_MODEL,
            messages=[
                {"role": "system", "content": "你是佛学资料摘要助手，用简体中文给出2-3句摘要。"},
                {"role": "user", "content": text[:8000]},
            ],
        )
        return resp.choices[0].message.content

    async def chat(self, messages: list[dict], context: str | None = None) -> str:
        if not self.is_configured:
            return "（OpenAI 未配置）"
        full_messages = messages
        if context:
            full_messages = [{"role": "system", "content": f"参考资料：\n{context}"}] + messages
        resp = await self._client.chat.completions.create(
            model=settings.AI_REASONING_MODEL,
            messages=full_messages,
        )
        return resp.choices[0].message.content


class OpenAISTTProvider(STTProvider):
    def __init__(self):
        self._client = None
        if settings.OPENAI_API_KEY:
            try:
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            except ImportError:
                self._client = None

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    async def transcribe(self, audio_path: str) -> dict:
        if not self.is_configured:
            return {"text": "", "segments": [], "status": "not_configured"}
        with open(audio_path, "rb") as f:
            resp = await self._client.audio.transcriptions.create(
                model=settings.STT_MODEL, file=f, response_format="verbose_json"
            )
        return {"text": resp.text, "segments": getattr(resp, "segments", []), "status": "completed"}


class OpenAITTSProvider(TTSProvider):
    def __init__(self):
        self._client = None
        if settings.OPENAI_API_KEY:
            try:
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            except ImportError:
                self._client = None

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    async def synthesize(self, text: str, out_path: str) -> bool:
        if not self.is_configured:
            return False
        async with self._client.audio.speech.with_streaming_response.create(
            model=settings.TTS_MODEL, voice="alloy", input=text
        ) as resp:
            await resp.stream_to_file(out_path)
        return True
