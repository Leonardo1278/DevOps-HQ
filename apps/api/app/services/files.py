from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.entities import CredentialRef, Document
from app.models.enums import ActivityAction, DocumentSource
from app.repositories.files import CredentialRepository, DocumentRepository
from app.schemas.core import CredentialCreate, DocumentCreate, DocumentPresignIn, DocumentPresignOut
from app.services.core import NotFoundError, ProjectService, record_activity
from app.services.storage import object_exists, presign_get, presign_put


class BadRequestError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


def _http_url(value: str) -> str:
    url = value.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        raise BadRequestError("source_url must start with http:// or https://")
    return url


class DocumentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = DocumentRepository(db)

    def get(self, document_id: uuid.UUID) -> Document:
        document = self.repo.get(document_id)
        if document is None:
            raise NotFoundError("document", document_id)
        return document

    def list(self, **kwargs):  # noqa: ANN003
        return self.repo.list(**kwargs)

    @staticmethod
    def presign(payload: DocumentPresignIn) -> DocumentPresignOut:
        result = presign_put(payload.filename, payload.content_type)
        return DocumentPresignOut(
            upload_url=result.upload_url,
            method=result.method,
            headers=result.headers,
            storage_key=result.storage_key,
            expires_in=result.expires_in,
        )

    def create(self, payload: DocumentCreate) -> Document:
        if payload.project_id:
            ProjectService(self.db).get(payload.project_id)
        if payload.source_type == DocumentSource.URL:
            if not payload.source_url:
                raise BadRequestError("source_url is required for URL documents")
            document = Document(
                title=payload.title.strip(),
                description=payload.description,
                project_id=payload.project_id,
                source_type=DocumentSource.URL.value,
                source_url=_http_url(payload.source_url),
                content_type=payload.content_type,
                size_bytes=payload.size_bytes,
            )
        else:
            if not payload.storage_key:
                raise BadRequestError("storage_key is required for S3 documents")
            if not object_exists(payload.storage_key):
                raise BadRequestError("Upload the file before creating the document")
            document = Document(
                title=payload.title.strip(),
                description=payload.description,
                project_id=payload.project_id,
                source_type=DocumentSource.S3.value,
                storage_key=payload.storage_key,
                content_type=payload.content_type,
                size_bytes=payload.size_bytes,
            )
        self.repo.add(document)
        record_activity(
            self.db,
            action=ActivityAction.CREATED,
            entity_type="document",
            entity_id=document.id,
            project_id=document.project_id,
            summary=f"Documento · {document.title}",
        )
        self.db.commit()
        self.db.refresh(document)
        return document

    def open_url(self, document_id: uuid.UUID) -> tuple[str, DocumentSource]:
        document = self.get(document_id)
        if document.source_type == DocumentSource.URL.value:
            if not document.source_url:
                raise BadRequestError("Document has no URL")
            return document.source_url, DocumentSource.URL
        if not document.storage_key:
            raise BadRequestError("Document has no storage_key")
        return presign_get(document.storage_key), DocumentSource.S3


class CredentialService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CredentialRepository(db)

    def get(self, credential_id: uuid.UUID) -> CredentialRef:
        item = self.repo.get(credential_id)
        if item is None:
            raise NotFoundError("credential", credential_id)
        return item

    def list(self, **kwargs):  # noqa: ANN003
        return self.repo.list(**kwargs)

    def create(self, payload: CredentialCreate) -> CredentialRef:
        if payload.project_id:
            ProjectService(self.db).get(payload.project_id)
        ref = payload.secret_ref.strip()
        if any(token in ref.lower() for token in ("password=", "secret=", "token=")):
            raise BadRequestError("secret_ref cannot contain a secret value")
        item = CredentialRef(
            name=payload.name.strip(),
            kind=payload.kind.value,
            secret_ref=ref,
            notes=payload.notes,
            project_id=payload.project_id,
        )
        self.repo.add(item)
        record_activity(
            self.db,
            action=ActivityAction.CREATED,
            entity_type="credential",
            entity_id=item.id,
            project_id=item.project_id,
            summary=f"Acceso · {item.name}",
        )
        self.db.commit()
        self.db.refresh(item)
        return item
