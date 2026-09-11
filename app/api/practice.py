from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.db import get_db
from app.models.models import PracticeSession

router = APIRouter(prefix="/api/practice", tags=["practice"])


class StartPracticeIn(BaseModel):
    practice_type: str
    target: int | None = None
    scripture_id: str | None = None


class StrikeIn(BaseModel):
    pass


@router.post("/start")
def start_practice(body: StartPracticeIn, db: Session = Depends(get_db)):
    session = PracticeSession(practice_type=body.practice_type, target=body.target, scripture_id=body.scripture_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return _serialize(session)


@router.post("/{session_id}/strike")
def strike(session_id: str, db: Session = Depends(get_db)):
    """木鱼/念珠/引磬统一敲击接口（规范51/52章）：计数+1，真正落库，刷新不丢失。"""
    session = db.query(PracticeSession).filter(PracticeSession.id == session_id).first()
    if not session:
        raise HTTPException(404, "修行记录不存在")
    session.count += 1
    if session.target and session.count >= session.target:
        session.completed = True
    db.commit()
    return _serialize(session)


@router.post("/{session_id}/finish")
def finish(session_id: str, db: Session = Depends(get_db)):
    session = db.query(PracticeSession).filter(PracticeSession.id == session_id).first()
    if not session:
        raise HTTPException(404, "修行记录不存在")
    session.end_time = datetime.utcnow()
    if session.start_time:
        session.duration_sec = int((session.end_time - session.start_time).total_seconds())
    db.commit()
    return _serialize(session)


@router.get("/today")
def today_sessions(db: Session = Depends(get_db)):
    today = datetime.utcnow().date()
    sessions = db.query(PracticeSession).filter(PracticeSession.start_time >= today).all()
    return [_serialize(s) for s in sessions]


@router.get("/session-of-day")
def get_or_create_today_session(practice_type: str, target: int | None = None, db: Session = Depends(get_db)):
    """按类型获取"今天进行中"的修行记录，没有则新建一条（规范51章）。
    前端木鱼/念珠/引磬刷新页面后应该拿到同一条记录继续累加，而不是每次刷新清零。
    """
    today = datetime.utcnow().date()
    session = (
        db.query(PracticeSession)
        .filter(
            PracticeSession.practice_type == practice_type,
            PracticeSession.start_time >= today,
            PracticeSession.end_time.is_(None),
        )
        .order_by(PracticeSession.start_time.desc())
        .first()
    )
    if not session:
        session = PracticeSession(practice_type=practice_type, target=target)
        db.add(session)
        db.commit()
        db.refresh(session)
    return _serialize(session)


def _serialize(s: PracticeSession) -> dict:
    return {
        "id": s.id,
        "practice_type": s.practice_type,
        "count": s.count,
        "target": s.target,
        "completed": s.completed,
        "start_time": s.start_time.isoformat() if s.start_time else None,
        "end_time": s.end_time.isoformat() if s.end_time else None,
        "duration_sec": s.duration_sec,
    }
