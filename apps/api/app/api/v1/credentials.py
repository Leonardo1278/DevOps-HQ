from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import db_session, pagination, raise_not_found
from app.models.enums import CredentialKind
from app.schemas.core import CredentialCreate, CredentialOut, Page
from app.services.core import NotFoundError
from app.services.files import BadRequestError, CredentialService

router = APIRouter(prefix="/credentials", tags=["credentials"])


@router.get("", response_model=Page[CredentialOut])
def list_credentials(
    project_id: UUID | None = None,
    kind: CredentialKind | None = None,
    q: str | None = Query(default=None),
    page: tuple[int, int] = Depends(pagination),
    db: Session = Depends(db_session),
) -> Page[CredentialOut]:
    limit, offset = page
    items, total = CredentialService(db).list(
        project_id=project_id,
        kind=kind.value if kind else None,
        q=q,
        limit=limit,
        offset=offset,
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=CredentialOut, status_code=201)
def create_credential(
    payload: CredentialCreate, db: Session = Depends(db_session)
) -> CredentialOut:
    try:
        return CredentialService(db).create(payload)
    except NotFoundError as exc:
        raise_not_found(exc)
        raise
    except BadRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{credential_id}", response_model=CredentialOut)
def get_credential(credential_id: UUID, db: Session = Depends(db_session)) -> CredentialOut:
    try:
        return CredentialService(db).get(credential_id)
    except NotFoundError as exc:
        raise_not_found(exc)
        raise
