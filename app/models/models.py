import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey

from app.models.db import Base


def gen_id() -> str:
    return uuid.uuid4().hex


class Resource(Base):
    """统一资源库条目（规范第34/44章）：经书/文档/音频/视频/图片/笔记 等一切资料的统一入口。"""

    __tablename__ = "resources"

    id = Column(String, primary_key=True, default=gen_id)
    source_type = Column(String, nullable=False)  # document | audio | video | image | note | webpage
    filename = Column(String, nullable=False)
    title = Column(String, nullable=True)
    author = Column(String, nullable=True)
    language = Column(String, nullable=True)
    mime_type = Column(String, nullable=True)
    checksum_sha256 = Column(String, index=True, nullable=True)
    size_bytes = Column(Integer, default=0)
    original_path = Column(String, nullable=True)  # storage/resources/<id>/original/<filename>
    text_content = Column(Text, nullable=True)  # 解析出的正文（供全文检索/朗读/摘要使用）
    summary = Column(Text, nullable=True)  # AI 摘要（未配置 AI 时为空，非"已生成但为空"）
    tags = Column(JSON, default=list)
    status = Column(String, default="processing")  # processing | completed | failed
    processing_steps = Column(JSON, default=list)  # [{step, status, error?}] 规范55/56章：每步进度+失败记录
    deleted_at = Column(DateTime, nullable=True)  # 软删除（规范46章回收站），非 None 即视为在回收站
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PracticeSession(Base):
    """修行记录（规范51章 Practice Engine）：木鱼/念珠/诵经/打坐/礼佛统一结构，不再各自乱存。"""

    __tablename__ = "practice_sessions"

    id = Column(String, primary_key=True, default=gen_id)
    practice_type = Column(String, nullable=False)  # muyu | beads | bell | sutra | meditate | bow
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_sec = Column(Integer, nullable=True)
    count = Column(Integer, default=0)
    target = Column(Integer, nullable=True)
    completed = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    media_id = Column(String, ForeignKey("resources.id"), nullable=True)
    scripture_id = Column(String, nullable=True)
    device = Column(String, nullable=True)


class Note(Base):
    """笔记（规范40/41章 Notes Service）：支持与媒体时间戳关联，而不只是一个 textarea。"""

    __tablename__ = "notes"

    id = Column(String, primary_key=True, default=gen_id)
    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    tags = Column(JSON, default=list)
    source_resource_id = Column(String, ForeignKey("resources.id"), nullable=True)
    source_timestamp_sec = Column(Float, nullable=True)  # 关联媒体的具体时间点
    favorited = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PlaybackState(Base):
    """播放/阅读进度（规范20/88/89章）：断点续播必须由后端+数据库管理，前端只是 View。"""

    __tablename__ = "playback_states"

    id = Column(String, primary_key=True, default=gen_id)
    resource_id = Column(String, ForeignKey("resources.id"), nullable=False)
    current_position_sec = Column(Float, default=0)
    duration_sec = Column(Float, nullable=True)
    completed = Column(Boolean, default=False)
    play_count = Column(Integer, default=0)
    last_played_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProcessingJob(Base):
    """后台任务（规范54/55/56章）：每个耗时处理都有独立任务记录，带进度与失败重试点。"""

    __tablename__ = "processing_jobs"

    id = Column(String, primary_key=True, default=gen_id)
    resource_id = Column(String, ForeignKey("resources.id"), nullable=True)
    job_type = Column(String, nullable=False)  # document_ingest | audio_ingest | video_ingest
    status = Column(String, default="queued")  # queued | running | completed | failed
    current_step = Column(String, nullable=True)
    progress_percent = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Connector(Base):
    """外部知识库/工作流连接器（规范78/79章 Adapter 架构落库存储配置与状态）。"""

    __tablename__ = "connectors"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    kind = Column(String, nullable=False)  # knowledge | workflow
    type = Column(String, nullable=False)  # obsidian | notion | n8n | webhook | rest_api | mcp ...
    status = Column(String, default="not_configured")  # not_configured | connected | error | syncing
    config_json = Column(JSON, default=dict)  # 非密钥类配置；密钥另存加密字段/环境变量，不落此表明文
    last_synced_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
