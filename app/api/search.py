from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.db import get_db
from app.models.models import Resource
from app.providers.factory import get_vector_provider

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
def search(q: str, db: Session = Depends(get_db)):
    """统一检索（规范73/74章）：当前是 Metadata + 本地关键词全文，向量语义检索取决于 VECTOR_PROVIDER。"""
    vector = get_vector_provider()
    hits = vector.search(q)
    results = []
    for hit in hits:
        r = db.query(Resource).filter(Resource.id == hit["resource_id"], Resource.deleted_at.is_(None)).first()
        if r:
            results.append({"id": r.id, "title": r.title, "source_type": r.source_type, "score": hit["score"]})
    return {"query": q, "results": results}
