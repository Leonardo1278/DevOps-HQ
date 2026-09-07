from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.v1.deps import db_session, pagination, raise_not_found
from app.models.enums import IdeaStatus
from app.schemas.core import IdeaCreate, IdeaOut, IdeaUpdate, Page
from app.services.core import IdeaService, NotFoundError

router = APIRouter(prefix="/ideas", tags=["ideas"])


@router.get("", response_model=Page[IdeaOut])
def list_ideas(
    project_id: UUID | None = None,
    status: IdeaStatus | None = None,
    q: str | None = Query(default=None),
    page: tuple[int, int] = Depends(pagination),
    db: Session = Depends(db_session),
) -> Page[IdeaOut]:
    limit, offset = page
    items, total = IdeaService(db).list(
        project_id=project_id,
        status=status.value if status else None,
        q=q,
        limit=limit,
        offset=offset,
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=IdeaOut, status_code=201)
def create_idea(payload: IdeaCreate, db: Session = Depends(db_session)) -> IdeaOut:
    try:
        return IdeaService(db).create(payload)
    except NotFoundError as exc:
        raise_not_found(exc)
        raise


@router.get("/{idea_id}", response_model=IdeaOut)
def get_idea(idea_id: UUID, db: Session = Depends(db_session)) -> IdeaOut:
    try:
        return IdeaService(db).get(idea_id)
    except NotFoundError as exc:
        raise_not_found(exc)
        raise


@router.patch("/{idea_id}", response_model=IdeaOut)
def update_idea(idea_id: UUID, payload: IdeaUpdate, db: Session = Depends(db_session)) -> IdeaOut:
    try:
        return IdeaService(db).update(idea_id, payload)
    except NotFoundError as exc:
        raise_not_found(exc)
        raise


@router.delete("/{idea_id}", status_code=204)
def delete_idea(idea_id: UUID, db: Session = Depends(db_session)) -> Response:
    try:
        IdeaService(db).delete(idea_id)
    except NotFoundError as exc:
        raise_not_found(exc)
        raise
    return Response(status_code=204)


@router.post("/{idea_id}/convert-to-task", response_model=IdeaOut)
def convert_idea(idea_id: UUID, db: Session = Depends(db_session)) -> IdeaOut:
    try:
        idea, _task = IdeaService(db).convert_to_task(idea_id)
        return idea
    except NotFoundError as exc:
        raise_not_found(exc)
        raise
