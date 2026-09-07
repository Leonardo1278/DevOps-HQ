from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import db_session, pagination, raise_not_found
from app.models.enums import DocumentSource
from app.schemas.core import (
    DocumentCreate,
    DocumentOut,
    DocumentPresignIn,
    DocumentPresignOut,
    DocumentUrlOut,
    Page,
)
from app.services.core import NotFoundError
from app.services.files import BadRequestError, DocumentService
from app.services.storage import StorageError

router = APIRouter(prefix="/documents", tags=["documents"])


def _raise_bad_request(exc: Exception) -> None:
    status = getattr(exc, "status_code", 400)
    raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.get("", response_model=Page[DocumentOut])
def list_documents(
    project_id: UUID | None = None,
    source_type: DocumentSource | None = None,
    q: str | None = Query(default=None),
    page: tuple[int, int] = Depends(pagination),
    db: Session = Depends(db_session),
) -> Page[DocumentOut]:
    limit, offset = page
    items, total = DocumentService(db).list(
        project_id=project_id,
        source_type=source_type.value if source_type else None,
        q=q,
        limit=limit,
        offset=offset,
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("/presign", response_model=DocumentPresignOut)
def presign_document(payload: DocumentPresignIn) -> DocumentPresignOut:
    try:
        return DocumentService.presign(payload)
    except StorageError as exc:
        _raise_bad_request(exc)
        raise


@router.post("", response_model=DocumentOut, status_code=201)
def create_document(payload: DocumentCreate, db: Session = Depends(db_session)) -> DocumentOut:
    try:
        return DocumentService(db).create(payload)
    except NotFoundError as exc:
        raise_not_found(exc)
        raise
    except (BadRequestError, StorageError) as exc:
        _raise_bad_request(exc)
        raise


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: UUID, db: Session = Depends(db_session)) -> DocumentOut:
    try:
        return DocumentService(db).get(document_id)
    except NotFoundError as exc:
        raise_not_found(exc)
        raise


@router.get("/{document_id}/url", response_model=DocumentUrlOut)
def document_url(document_id: UUID, db: Session = Depends(db_session)) -> DocumentUrlOut:
    try:
        url, source_type = DocumentService(db).open_url(document_id)
        return DocumentUrlOut(url=url, source_type=source_type)
    except NotFoundError as exc:
        raise_not_found(exc)
        raise
    except (BadRequestError, StorageError) as exc:
        _raise_bad_request(exc)
        raise
