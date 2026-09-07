from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import db_session, pagination, raise_conflict, raise_not_found
from app.models.enums import InboxType
from app.schemas.core import InboxClassify, InboxConvert, InboxCreate, InboxOut, Page
from app.services.core import ConflictError, InboxService, NotFoundError

router = APIRouter(prefix="/inbox", tags=["inbox"])


@router.get("", response_model=Page[InboxOut])
def list_inbox(
    project_id: UUID | None = None,
    item_type: InboxType | None = None,
    include_converted: bool = False,
    q: str | None = Query(default=None),
    page: tuple[int, int] = Depends(pagination),
    db: Session = Depends(db_session),
) -> Page[InboxOut]:
    limit, offset = page
    items, total = InboxService(db).list(
        project_id=project_id,
        item_type=item_type.value if item_type else None,
        include_converted=include_converted,
        q=q,
        limit=limit,
        offset=offset,
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=InboxOut, status_code=201)
def create_inbox(payload: InboxCreate, db: Session = Depends(db_session)) -> InboxOut:
    try:
        return InboxService(db).create(payload)
    except NotFoundError as exc:
        raise_not_found(exc)
        raise


@router.get("/{item_id}", response_model=InboxOut)
def get_inbox(item_id: UUID, db: Session = Depends(db_session)) -> InboxOut:
    try:
        return InboxService(db).get(item_id)
    except NotFoundError as exc:
        raise_not_found(exc)
        raise


@router.post("/{item_id}/classify", response_model=InboxOut)
def classify_inbox(
    item_id: UUID,
    payload: InboxClassify,
    db: Session = Depends(db_session),
) -> InboxOut:
    try:
        return InboxService(db).classify(item_id, payload)
    except NotFoundError as exc:
        raise_not_found(exc)
        raise
    except ConflictError as exc:
        raise_conflict(exc)
        raise


@router.post("/{item_id}/convert", response_model=InboxOut)
def convert_inbox(
    item_id: UUID,
    payload: InboxConvert,
    db: Session = Depends(db_session),
) -> InboxOut:
    try:
        return InboxService(db).convert(item_id, payload)
    except NotFoundError as exc:
        raise_not_found(exc)
        raise
    except ConflictError as exc:
        raise_conflict(exc)
        raise
