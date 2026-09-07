from collections.abc import Generator
from uuid import UUID

from fastapi import HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.core import ConflictError, NotFoundError


def db_session() -> Generator[Session, None, None]:
    yield from get_db()


def pagination(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> tuple[int, int]:
    return limit, offset


def raise_not_found(exc: NotFoundError) -> None:
    raise HTTPException(status_code=404, detail=str(exc)) from exc


def raise_conflict(exc: ConflictError) -> None:
    raise HTTPException(status_code=409, detail=str(exc)) from exc


def parse_uuid(value: str, name: str = "id") -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid {name}") from exc
