"""
Provider 抽象接口（规范第99章）：AI/STT/TTS/OCR/Vector/Storage 全部可替换，
核心业务逻辑只依赖这些接口，不直接依赖某个具体供应商（如 OpenAI）。
"""
from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    async def summarize(self, text: str) -> str | None: ...

    @abstractmethod
    async def chat(self, messages: list[dict], context: str | None = None) -> str: ...

    @property
    @abstractmethod
    def is_configured(self) -> bool: ...


class STTProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio_path: str) -> dict: ...

    @property
    @abstractmethod
    def is_configured(self) -> bool: ...


class TTSProvider(ABC):
    @abstractmethod
    async def synthesize(self, text: str, out_path: str) -> bool: ...

    @property
    @abstractmethod
    def is_configured(self) -> bool: ...


class VectorProvider(ABC):
    @abstractmethod
    def index(self, resource_id: str, text: str) -> None: ...

    @abstractmethod
    def search(self, query: str, top_k: int = 10) -> list[dict]: ...
