from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import db_session, raise_not_found
from app.schemas.core import NoteOut
from app.services.core import NotFoundError, NoteService

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("/{note_id}", response_model=NoteOut)
def get_note(note_id: UUID, db: Session = Depends(db_session)) -> NoteOut:
    try:
        return NoteService(db).get(note_id)
    except NotFoundError as exc:
        raise_not_found(exc)
        raise
