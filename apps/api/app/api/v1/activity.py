from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import db_session, pagination
from app.schemas.core import ActivityOut, Page
from app.services.core import ActivityService

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("", response_model=Page[ActivityOut])
def list_activity(
    project_id: UUID | None = None,
    page: tuple[int, int] = Depends(pagination),
    db: Session = Depends(db_session),
) -> Page[ActivityOut]:
    limit, offset = page
    items, total = ActivityService(db).list(project_id=project_id, limit=limit, offset=offset)
    return Page(items=items, total=total, limit=limit, offset=offset)
