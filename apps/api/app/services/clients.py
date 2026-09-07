from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models.entities import Client, Project
from app.models.enums import ActivityAction, ClientStatus
from app.repositories.clients import ClientRepository
from app.schemas.core import ClientCreate, ClientUpdate
from app.services.core import NotFoundError, record_activity, slugify

KNOWN_CLIENTS: list[tuple[str, tuple[str, ...], str]] = [
    ("PROTEM", ("PROTEM", "PROTEM App"), "Plataforma regulatoria y app móvil"),
    ("ENVOLVEX", ("ENVOLVEX", "ENVOLVEX Packaging"), "CRM, ventas y línea de empaque"),
    ("Drop Universe", ("Drop Universe",), "E-commerce"),
    ("DataQube", ("DataQube",), "Plataforma de datos"),
]


def unique_client_slug(repo: ClientRepository, name: str, exclude_id: uuid.UUID | None = None) -> str:
    base = slugify(name)
    candidate = base
    suffix = 2
    while True:
        existing = repo.get_by_slug(candidate)
        if existing is None or (exclude_id and existing.id == exclude_id):
            return candidate
        candidate = f"{base}-{suffix}"
        suffix += 1


class ClientService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ClientRepository(db)

    def get(self, client_id: uuid.UUID) -> Client:
        client = self.repo.get(client_id)
        if client is None:
            raise NotFoundError("client", client_id)
        return client

    def list(self, **kwargs):  # noqa: ANN003
        return self.repo.list(**kwargs)

    def _assign_projects(self, client: Client, project_ids: list[uuid.UUID]) -> None:
        wanted = set(project_ids)
        for project in list(self.db.scalars(select(Project).where(Project.client_id == client.id))):
            if project.id not in wanted:
                project.client_id = None
        for project_id in wanted:
            project = self.db.get(Project, project_id)
            if project is None:
                raise NotFoundError("project", project_id)
            project.client_id = client.id

    def create(self, payload: ClientCreate) -> Client:
        client = Client(
            name=payload.name.strip(),
            slug=unique_client_slug(self.repo, payload.name),
            notes=payload.notes,
            status=payload.status.value,
        )
        self.repo.add(client)
        if payload.project_ids:
            self._assign_projects(client, payload.project_ids)
        record_activity(
            self.db,
            action=ActivityAction.CREATED,
            entity_type="client",
            entity_id=client.id,
            summary=f"Cliente creado · {client.name}",
        )
        self.db.commit()
        return self.get(client.id)

    def update(self, client_id: uuid.UUID, payload: ClientUpdate) -> Client:
        client = self.get(client_id)
        data = payload.model_dump(exclude_unset=True)
        if "name" in data and data["name"] is not None:
            new_name = data["name"].strip()
            if new_name != client.name:
                client.name = new_name
                client.slug = unique_client_slug(self.repo, new_name, exclude_id=client.id)
        if "notes" in data:
            client.notes = data["notes"]
        if "status" in data and data["status"] is not None:
            client.status = data["status"].value
        if "project_ids" in data and data["project_ids"] is not None:
            self._assign_projects(client, data["project_ids"])
        client.updated_at = utcnow()
        record_activity(
            self.db,
            action=ActivityAction.UPDATED,
            entity_type="client",
            entity_id=client.id,
            summary=f"Cliente actualizado · {client.name}",
        )
        self.db.commit()
        return self.get(client.id)

    def delete(self, client_id: uuid.UUID) -> None:
        client = self.get(client_id)
        record_activity(
            self.db,
            action=ActivityAction.DELETED,
            entity_type="client",
            entity_id=client.id,
            summary=f"Cliente borrado · {client.name}",
        )
        self.repo.delete(client)
        self.db.commit()

    def sync_from_projects(self) -> list[Client]:
        projects = list(self.db.scalars(select(Project)))
        claimed: set[uuid.UUID] = set()
        for name, aliases, notes in KNOWN_CLIENTS:
            matches = [item for item in projects if item.name in aliases]
            if not matches:
                continue
            client = self.repo.get_by_name(name)
            if client is None:
                client = Client(
                    name=name,
                    slug=unique_client_slug(self.repo, name),
                    notes=notes,
                    status=ClientStatus.ACTIVE.value,
                )
                self.repo.add(client)
            for project in matches:
                project.client_id = client.id
                claimed.add(project.id)
        self.db.commit()
        items, _ = self.repo.list(q=None, status=None, limit=100, offset=0)
        return items
