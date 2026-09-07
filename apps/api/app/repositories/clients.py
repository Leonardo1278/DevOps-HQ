from __future__ import annotations

import uuid

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.entities import Client


class ClientRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, client_id: uuid.UUID) -> Client | None:
        return self.db.scalar(
            select(Client).options(selectinload(Client.projects)).where(Client.id == client_id)
        )

    def get_by_slug(self, slug: str) -> Client | None:
        return self.db.scalar(select(Client).where(Client.slug == slug))

    def get_by_name(self, name: str) -> Client | None:
        return self.db.scalar(select(Client).where(Client.name == name))

    def list(
        self,
        *,
        q: str | None,
        status: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Client], int]:
        stmt: Select[tuple[Client]] = select(Client).options(selectinload(Client.projects))
        count_stmt: Select[tuple[int]] = select(func.count()).select_from(Client)
        if status:
            stmt = stmt.where(Client.status == status)
            count_stmt = count_stmt.where(Client.status == status)
        if q:
            pattern = f"%{q}%"
            filt = or_(Client.name.ilike(pattern), Client.notes.ilike(pattern))
            stmt = stmt.where(filt)
            count_stmt = count_stmt.where(filt)
        total = self.db.scalar(count_stmt) or 0
        items = list(
            self.db.scalars(stmt.order_by(Client.name.asc()).limit(limit).offset(offset))
        )
        return items, total

    def add(self, client: Client) -> Client:
        self.db.add(client)
        self.db.flush()
        return client

    def delete(self, client: Client) -> None:
        self.db.delete(client)
