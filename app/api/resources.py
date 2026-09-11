import os
import tempfile
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.models.db import get_db
from app.models.models import Resource
from app.services.ingestion import ingest_document

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """统一文件入口（V4规范第3章）：不要求用户说明类型，系统自己判断并处理。"""
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    resource = await ingest_document(db, tmp_path, file.filename)
    return _serialize(resource)


@router.get("")
def list_resources(source_type: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Resource).filter(Resource.deleted_at.is_(None))
    if source_type:
        q = q.filter(Resource.source_type == source_type)
    return [_serialize(r) for r in q.order_by(Resource.created_at.desc()).all()]


@router.get("/{resource_id}")
def get_resource(resource_id: str, db: Session = Depends(get_db)):
    r = db.query(Resource).filter(Resource.id == resource_id).first()
    if not r:
        raise HTTPException(404, "资源不存在")
    return _serialize(r)


@router.delete("/{resource_id}")
def soft_delete(resource_id: str, db: Session = Depends(get_db)):
    """软删除进回收站（规范46/47章），不直接物理删除。"""
    r = db.query(Resource).filter(Resource.id == resource_id).first()
    if not r:
        raise HTTPException(404, "资源不存在")
    r.deleted_at = datetime.utcnow()
    db.commit()
    return {"ok": True}


@router.post("/{resource_id}/restore")
def restore(resource_id: str, db: Session = Depends(get_db)):
    r = db.query(Resource).filter(Resource.id == resource_id).first()
    if not r:
        raise HTTPException(404, "资源不存在")
    r.deleted_at = None
    db.commit()
    return _serialize(r)


def _serialize(r: Resource) -> dict:
    return {
        "id": r.id,
        "source_type": r.source_type,
        "filename": r.filename,
        "title": r.title,
        "status": r.status,
        "summary": r.summary,
        "tags": r.tags,
        "size_bytes": r.size_bytes,
        "processing_steps": r.processing_steps,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }
