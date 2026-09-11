import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ai, health, notes, practice, resources, search
from app.core.config import get_settings
from app.models.db import Base, engine

settings = get_settings()

# --- 独立日志目录（规范第84条：不与其它项目共用日志） ---
os.makedirs(settings.LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(settings.LOG_DIR, "app.log"), encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("buddhist_studio")

os.makedirs(settings.STORAGE_ROOT, exist_ok=True)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="佛学工作室后端 API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本地开发用；生产环境应改为前端实际域名白名单
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resources.router)
app.include_router(practice.router)
app.include_router(notes.router)
app.include_router(search.router)
app.include_router(health.router)
app.include_router(ai.router)


@app.on_event("startup")
def startup_health_check():
    """规范第82条：启动时自动检测各依赖并明确报出问题，不要等用到才发现。"""
    from app.providers.factory import get_ai_provider, get_stt_provider, get_tts_provider, get_vector_provider
    from app.models.db import SessionLocal
    from app.models.models import Resource

    logger.info("=== 佛学工作室后端启动健康检查 ===")
    logger.info("Database: connected (%s)", settings.DATABASE_URL)
    logger.info("Storage: connected (%s)", settings.STORAGE_ROOT)
    ai_p, stt_p, tts_p = get_ai_provider(), get_stt_provider(), get_tts_provider()
    logger.info("AI Provider: %s", "connected" if ai_p.is_configured else "NOT CONFIGURED (设置 .env 的 OPENAI_API_KEY 后启用)")
    logger.info("STT Provider: %s", "connected" if stt_p.is_configured else "NOT CONFIGURED")
    logger.info("TTS Provider: %s", "connected" if tts_p.is_configured else "NOT CONFIGURED")

    # 本地关键词索引是内存态，重启会丢失，这里从数据库里已有的正文重新建一遍（规范89条：状态不能丢）
    vector = get_vector_provider()
    db = SessionLocal()
    try:
        resources = db.query(Resource).filter(Resource.deleted_at.is_(None), Resource.text_content.isnot(None)).all()
        for r in resources:
            vector.index(r.id, r.text_content)
        logger.info("Vector Provider: %s (本地关键词检索占位，已重建 %d 条索引)", settings.VECTOR_PROVIDER, len(resources))
    finally:
        db.close()
    logger.info("=== 健康检查完成，服务已就绪 ===")


@app.get("/")
def root():
    return {"service": "buddhist-studio-backend", "status": "ok", "docs": "/docs"}
