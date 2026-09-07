from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.v1.deps import db_session, pagination, raise_not_found
from app.models.enums import Priority, ProjectStatus
from app.repositories.core import PROJECT_SORTS
from app.schemas.core import Page, ProjectCreate, ProjectOut, ProjectUpdate
from app.services.core import NotFoundError, ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=Page[ProjectOut])
def list_projects(
    status: ProjectStatus | None = None,
    priority: Priority | None = None,
    q: str | None = Query(default=None),
    include_archived: bool = False,
    sort: str = Query(default="updated"),
    page: tuple[int, int] = Depends(pagination),
    db: Session = Depends(db_session),
) -> Page[ProjectOut]:
    limit, offset = page
    order = sort if sort in PROJECT_SORTS else "updated"
    items, total = ProjectService(db).list(
        status=status.value if status else None,
        priority=priority.value if priority else None,
        q=q,
        include_archived=include_archived,
        sort=order,
        limit=limit,
        offset=offset,
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(db_session)) -> ProjectOut:
    return ProjectService(db).create(payload)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: UUID, db: Session = Depends(db_session)) -> ProjectOut:
    try:
        return ProjectService(db).get(project_id)
    except NotFoundError as exc:
        raise_not_found(exc)
        raise


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: UUID, payload: ProjectUpdate, db: Session = Depends(db_session)
) -> ProjectOut:
    try:
        return ProjectService(db).update(project_id, payload)
    except NotFoundError as exc:
        raise_not_found(exc)
        raise


@router.delete("/{project_id}", response_model=ProjectOut)
def archive_project(project_id: UUID, db: Session = Depends(db_session)) -> ProjectOut:
    try:
        return ProjectService(db).archive(project_id)
    except NotFoundError as exc:
        raise_not_found(exc)
        raise


@router.post("/{project_id}/purge", status_code=204)
def purge_project(project_id: UUID, db: Session = Depends(db_session)) -> Response:
    try:
        ProjectService(db).purge(project_id)
    except NotFoundError as exc:
        raise_not_found(exc)
        raise
    return Response(status_code=204)
