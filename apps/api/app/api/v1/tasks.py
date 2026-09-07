from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.v1.deps import db_session, pagination, raise_not_found
from app.models.enums import Priority, TaskStatus
from app.schemas.core import Page, TaskCreate, TaskOut, TaskUpdate
from app.services.core import NotFoundError, TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=Page[TaskOut])
def list_tasks(
    project_id: UUID | None = None,
    status: TaskStatus | None = None,
    priority: Priority | None = None,
    q: str | None = Query(default=None),
    page: tuple[int, int] = Depends(pagination),
    db: Session = Depends(db_session),
) -> Page[TaskOut]:
    limit, offset = page
    items, total = TaskService(db).list(
        project_id=project_id,
        status=status.value if status else None,
        priority=priority.value if priority else None,
        q=q,
        limit=limit,
        offset=offset,
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=TaskOut, status_code=201)
def create_task(payload: TaskCreate, db: Session = Depends(db_session)) -> TaskOut:
    try:
        return TaskService(db).create(payload)
    except NotFoundError as exc:
        raise_not_found(exc)
        raise


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: UUID, db: Session = Depends(db_session)) -> TaskOut:
    try:
        return TaskService(db).get(task_id)
    except NotFoundError as exc:
        raise_not_found(exc)
        raise


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(task_id: UUID, payload: TaskUpdate, db: Session = Depends(db_session)) -> TaskOut:
    try:
        return TaskService(db).update(task_id, payload)
    except NotFoundError as exc:
        raise_not_found(exc)
        raise


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: UUID, db: Session = Depends(db_session)) -> Response:
    try:
        TaskService(db).delete(task_id)
    except NotFoundError as exc:
        raise_not_found(exc)
        raise
    return Response(status_code=204)


@router.post("/{task_id}/complete", response_model=TaskOut)
def complete_task(task_id: UUID, db: Session = Depends(db_session)) -> TaskOut:
    try:
        return TaskService(db).complete(task_id)
    except NotFoundError as exc:
        raise_not_found(exc)
        raise
