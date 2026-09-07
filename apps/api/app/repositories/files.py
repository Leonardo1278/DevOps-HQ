from __future__ import annotations

import uuid

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.entities import CredentialRef, Document


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, document_id: uuid.UUID) -> Document | None:
        return self.db.get(Document, document_id)

    def list(
        self,
        *,
        project_id: uuid.UUID | None,
        source_type: str | None,
        q: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Document], int]:
        stmt: Select[tuple[Document]] = select(Document)
        count_stmt: Select[tuple[int]] = select(func.count()).select_from(Document)
        if project_id:
            stmt = stmt.where(Document.project_id == project_id)
            count_stmt = count_stmt.where(Document.project_id == project_id)
        if source_type:
            stmt = stmt.where(Document.source_type == source_type)
            count_stmt = count_stmt.where(Document.source_type == source_type)
        if q:
            pattern = f"%{q}%"
            filt = or_(Document.title.ilike(pattern), Document.description.ilike(pattern))
            stmt = stmt.where(filt)
            count_stmt = count_stmt.where(filt)
        total = self.db.scalar(count_stmt) or 0
        items = list(
            self.db.scalars(stmt.order_by(Document.created_at.desc()).limit(limit).offset(offset))
        )
        return items, total

    def add(self, document: Document) -> Document:
        self.db.add(document)
        self.db.flush()
        return document


class CredentialRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, credential_id: uuid.UUID) -> CredentialRef | None:
        return self.db.get(CredentialRef, credential_id)

    def list(
        self,
        *,
        project_id: uuid.UUID | None,
        kind: str | None,
        q: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[CredentialRef], int]:
        stmt = select(CredentialRef)
        count_stmt = select(func.count()).select_from(CredentialRef)
        if project_id:
            stmt = stmt.where(CredentialRef.project_id == project_id)
            count_stmt = count_stmt.where(CredentialRef.project_id == project_id)
        if kind:
            stmt = stmt.where(CredentialRef.kind == kind)
            count_stmt = count_stmt.where(CredentialRef.kind == kind)
        if q:
            pattern = f"%{q}%"
            filt = or_(
                CredentialRef.name.ilike(pattern),
                CredentialRef.secret_ref.ilike(pattern),
            )
            stmt = stmt.where(filt)
            count_stmt = count_stmt.where(filt)
        total = self.db.scalar(count_stmt) or 0
        items = list(
            self.db.scalars(
                stmt.order_by(CredentialRef.created_at.desc()).limit(limit).offset(offset)
            )
        )
        return items, total

    def add(self, item: CredentialRef) -> CredentialRef:
        self.db.add(item)
        self.db.flush()
        return item
