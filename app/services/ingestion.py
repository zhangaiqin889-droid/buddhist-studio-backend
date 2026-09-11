"""
Universal File Ingestion Engine（V4规范第3-8、92章）。
流程：Upload → MIME检测 → SHA256 → 重复检测 → 按格式解析 → 文字清理 →
      (AI摘要，未配置时留空) → 向量索引 → 写入 Resource + ProcessingJob。

当前已真实实现（不需要任何付费 API Key）：
  - TXT / Markdown：直接读取
  - DOCX：python-docx 解析段落
  - PDF（文字版）：pypdf 逐页提取文字
真实但依赖后续接入（会在返回结果里如实标注，不假装完成）：
  - 扫描版 PDF 的 OCR（V4规范第7章）—— 需要额外装 OCR 引擎，当前返回 needs_ocr 状态
  - AI 摘要/关键词/佛学标签 —— 取决于 AI_PROVIDER 是否配置
"""
import hashlib
import mimetypes
import os
import shutil
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.models import ProcessingJob, Resource
from app.providers.factory import get_ai_provider, get_vector_provider

settings = get_settings()

SUPPORTED_DOCUMENT_EXT = {".txt", ".md", ".markdown", ".docx", ".pdf"}


def _sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _extract_text(path: str, ext: str) -> tuple[str, str]:
    """返回 (正文, 状态)。状态: completed | needs_ocr | unsupported"""
    if ext in (".txt", ".md", ".markdown"):
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(), "completed"

    if ext == ".docx":
        import docx

        d = docx.Document(path)
        text = "\n".join(p.text for p in d.paragraphs)
        return text, "completed"

    if ext == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(path)
        pages_text = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages_text)
        if not text.strip():
            # 扫描版 PDF，没有可提取文字 —— 如实标记，不假装已完成（规范第7、104条）
            return "", "needs_ocr"
        return text, "completed"

    return "", "unsupported"


async def ingest_document(db: Session, tmp_path: str, original_filename: str) -> Resource:
    ext = os.path.splitext(original_filename)[1].lower()
    mime_type, _ = mimetypes.guess_type(original_filename)
    checksum = _sha256_of_file(tmp_path)

    # 重复文件检测（规范第16章）
    existing = (
        db.query(Resource)
        .filter(Resource.checksum_sha256 == checksum, Resource.deleted_at.is_(None))
        .first()
    )
    if existing:
        os.remove(tmp_path)
        return existing

    resource = Resource(
        source_type="document",
        filename=original_filename,
        title=os.path.splitext(original_filename)[0],
        mime_type=mime_type,
        checksum_sha256=checksum,
        size_bytes=os.path.getsize(tmp_path),
        status="processing",
        processing_steps=[{"step": "upload", "status": "completed"}],
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)

    job = ProcessingJob(resource_id=resource.id, job_type="document_ingest", status="running", current_step="parse")
    db.add(job)
    db.commit()

    # 落地到统一资源目录结构（规范64章）
    resource_dir = os.path.join(settings.STORAGE_ROOT, resource.id, "original")
    os.makedirs(resource_dir, exist_ok=True)
    final_path = os.path.join(resource_dir, original_filename)
    shutil.move(tmp_path, final_path)
    resource.original_path = final_path

    if ext not in SUPPORTED_DOCUMENT_EXT:
        resource.status = "failed"
        resource.processing_steps.append({"step": "parse", "status": "failed", "error": f"暂不支持的格式: {ext}"})
        job.status = "failed"
        job.error_message = f"暂不支持的格式: {ext}"
        db.commit()
        return resource

    try:
        text, parse_status = _extract_text(final_path, ext)
    except Exception as e:  # 真实失败必须如实记录，不允许静默吞掉（规范第56、104条）
        resource.status = "failed"
        resource.processing_steps.append({"step": "parse", "status": "failed", "error": str(e)})
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
        return resource

    if parse_status == "needs_ocr":
        resource.status = "failed"
        resource.processing_steps.append(
            {"step": "parse", "status": "failed", "error": "扫描版PDF，需要OCR引擎（尚未接入，见V4规范第7章）"}
        )
        job.status = "failed"
        job.current_step = "ocr_required"
        job.error_message = "扫描版PDF，需要OCR引擎（尚未接入）"
        db.commit()
        return resource

    resource.text_content = text
    resource.processing_steps.append({"step": "parse", "status": "completed"})
    job.current_step = "summarize"
    job.progress_percent = 60
    db.commit()

    ai = get_ai_provider()
    resource.summary = await ai.summarize(text)
    resource.processing_steps.append(
        {"step": "summarize", "status": "completed" if ai.is_configured else "skipped_not_configured"}
    )

    vector = get_vector_provider()
    vector.index(resource.id, text)
    resource.processing_steps.append({"step": "vector_index", "status": "completed"})

    resource.status = "completed"
    resource.updated_at = datetime.utcnow()
    job.status = "completed"
    job.progress_percent = 100
    job.current_step = "done"
    db.commit()
    db.refresh(resource)
    return resource
