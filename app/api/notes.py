from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.db import get_db
from app.models.models import Note

router = APIRouter(prefix="/api/notes", tags=["notes"])


class NoteIn(BaseModel):
    title: str | None = None
    content: str
    tags: list[str] = []
    source_resource_id: str | None = None
    source_timestamp_sec: float | None = None


@router.post("")
def create_note(body: NoteIn, db: Session = Depends(get_db)):
    note = Note(**body.model_dump())
    db.add(note)
    db.commit()
    db.refresh(note)
    return _serialize(note)


@router.get("")
def list_notes(db: Session = Depends(get_db)):
    notes = db.query(Note).filter(Note.deleted_at.is_(None)).order_by(Note.updated_at.desc()).all()
    return [_serialize(n) for n in notes]


@router.patch("/{note_id}")
def update_note(note_id: str, body: NoteIn, db: Session = Depends(get_db)):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(404, "笔记不存在")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(note, k, v)
    db.commit()
    return _serialize(note)


def _serialize(n: Note) -> dict:
    return {
        "id": n.id,
        "title": n.title,
        "content": n.content,
        "tags": n.tags,
        "source_resource_id": n.source_resource_id,
        "source_timestamp_sec": n.source_timestamp_sec,
        "favorited": n.favorited,
        "created_at": n.created_at.isoformat() if n.created_at else None,
    }
