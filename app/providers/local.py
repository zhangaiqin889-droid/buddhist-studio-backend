"""
本地免费实现：不依赖任何付费 API Key，保证系统在没有配置 OpenAI 之前也能完整运行
（规范第100条验收原则：不允许"没连上却显示已连接"，所以这里如实标注 is_configured=False，
调用方看到 False 就不会在 UI 上显示绿色 Connected）。
"""
import re

from app.providers.base import AIProvider, STTProvider, TTSProvider, VectorProvider


class NoopAIProvider(AIProvider):
    """未配置 OpenAI 时的占位实现：不假装智能，只做确定性的轻量摘要，明确标注未接入真实AI。"""

    @property
    def is_configured(self) -> bool:
        return False

    async def summarize(self, text: str) -> str | None:
        if not text:
            return None
        # 简单启发式摘要：取前两句作为占位，真实摘要需要接入 AI_PROVIDER=openai
        sentences = re.split(r"[。！？.!?]", text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        return "。".join(sentences[:2]) + ("。" if sentences else "")

    async def chat(self, messages: list[dict], context: str | None = None) -> str:
        return "（AI 老师尚未配置 OpenAI API Key，暂时无法生成真实回答。请在设置中配置后重试。）"


class NoopSTTProvider(STTProvider):
    @property
    def is_configured(self) -> bool:
        return False

    async def transcribe(self, audio_path: str) -> dict:
        return {"text": "", "segments": [], "status": "not_configured"}


class NoopTTSProvider(TTSProvider):
    @property
    def is_configured(self) -> bool:
        return False

    async def synthesize(self, text: str, out_path: str) -> bool:
        return False


class LocalKeywordVectorProvider(VectorProvider):
    """本地关键词检索占位（规范第33/73章 VectorProvider 接口的一种实现）：
    未接 pgvector / OpenAI Embedding 时，用简单的词频匹配代替语义检索，
    保证"搜索"功能在没有向量库时也能真实工作，而不是直接报错或返回假数据。
    """

    def __init__(self):
        self._index: dict[str, str] = {}

    def index(self, resource_id: str, text: str) -> None:
        self._index[resource_id] = text or ""

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        query = query.strip().lower()
        if not query:
            return []
        scored = []
        for rid, text in self._index.items():
            text_lower = text.lower()
            # 子串计数：对中文更实用（中文没有天然空格分词，\w+ 整段会被当成一个词）
            score = text_lower.count(query)
            if score == 0:
                # 退化匹配：查询词里只要有一半以上字符在原文中出现也给个低分，避免完全漏检
                hit_chars = sum(1 for ch in set(query) if ch in text_lower)
                if len(query) > 1 and hit_chars >= max(1, len(set(query)) // 2):
                    score = hit_chars * 0.1
            if score > 0:
                scored.append({"resource_id": rid, "score": score})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]
