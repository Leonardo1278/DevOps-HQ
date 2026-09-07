"""Seed local demo projects/tasks/ideas. Safe to re-run: skips if projects exist."""

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.entities import Document, InboxItem, Project
from app.models.enums import (
    CredentialKind,
    DocumentSource,
    Effort,
    IdeaStatus,
    Impact,
    InboxType,
    Priority,
    ProjectHealth,
    ProjectStatus,
    TaskStatus,
)
from app.schemas.core import (
    CredentialCreate,
    DocumentCreate,
    IdeaCreate,
    InboxCreate,
    ProjectCreate,
    TaskCreate,
)
from app.services.clients import ClientService
from app.services.core import IdeaService, InboxService, ProjectService, TaskService
from app.services.files import CredentialService, DocumentService

SEED_PROJECTS: list[ProjectCreate] = [
    ProjectCreate(
        name="PROTEM",
        description="Plataforma regulatoria",
        status=ProjectStatus.ACTIVE,
        priority=Priority.HIGH,
        health=ProjectHealth.GOOD,
        progress_pct=78,
        color="#38bdf8",
        icon="P",
    ),
    ProjectCreate(
        name="ENVOLVEX",
        description="CRM & Ventas",
        status=ProjectStatus.ACTIVE,
        priority=Priority.HIGH,
        health=ProjectHealth.GOOD,
        progress_pct=64,
        color="#34d399",
        icon="E",
    ),
    ProjectCreate(
        name="ENVOLVEX Packaging",
        description="E-commerce de empaque",
        status=ProjectStatus.ACTIVE,
        priority=Priority.MEDIUM,
        health=ProjectHealth.RISK,
        progress_pct=48,
        color="#a78bfa",
        icon="EP",
    ),
    ProjectCreate(
        name="Drop Universe",
        description="E-commerce",
        status=ProjectStatus.ACTIVE,
        priority=Priority.MEDIUM,
        health=ProjectHealth.GOOD,
        progress_pct=72,
        color="#818cf8",
        icon="D",
    ),
    ProjectCreate(
        name="DataQube",
        description="Plataforma de datos",
        status=ProjectStatus.ACTIVE,
        priority=Priority.HIGH,
        health=ProjectHealth.RISK,
        progress_pct=35,
        color="#fbbf24",
        icon="DQ",
    ),
    ProjectCreate(
        name="PROTEM App",
        description="App móvil",
        status=ProjectStatus.PAUSED,
        priority=Priority.MEDIUM,
        health=ProjectHealth.BLOCKED,
        progress_pct=22,
        color="#fb923c",
        icon="PA",
    ),
]


def _seed_inbox(db, projects: dict[str, Project]) -> None:
    if db.scalar(select(InboxItem.id).limit(1)):
        return
    needed = ("PROTEM", "ENVOLVEX Packaging", "DataQube")
    if any(name not in projects for name in needed):
        return
    InboxService(db).create(
        InboxCreate(
            content="Integrar facturación automática en PROTEM",
            item_type=InboxType.TASK,
            project_id=projects["PROTEM"].id,
        )
    )
    InboxService(db).create(
        InboxCreate(
            content="Nueva idea de empaque para florerías",
            item_type=InboxType.IDEA,
            project_id=projects["ENVOLVEX Packaging"].id,
        )
    )
    InboxService(db).create(
        InboxCreate(
            content="Revisar versión nueva de la web de DataQube",
            item_type=InboxType.NOTE,
            project_id=projects["DataQube"].id,
        )
    )


def _seed_files(db, projects: dict[str, Project]) -> None:
    if db.scalar(select(Document.id).limit(1)):
        return
    if "PROTEM" not in projects or "DataQube" not in projects:
        return
    DocumentService(db).create(
        DocumentCreate(
            title="NOM-019 borrador",
            description="Enlace al brief, sin binario en Postgres.",
            project_id=projects["PROTEM"].id,
            source_type=DocumentSource.URL,
            source_url="https://example.com/protem/nom-019",
        )
    )
    CredentialService(db).create(
        CredentialCreate(
            name="DataQube RDS",
            kind=CredentialKind.DATABASE,
            secret_ref="arn:aws:secretsmanager:us-east-1:000000000000:secret:leo/dataqube/rds",
            project_id=projects["DataQube"].id,
            notes="Solo el ARN. El valor vive en Secrets Manager.",
        )
    )


def run() -> None:
    db = SessionLocal()
    try:
        existing = list(db.scalars(select(Project)))
        if existing:
            projects = {item.name: item for item in existing}
            _seed_inbox(db, projects)
            _seed_files(db, projects)
            ClientService(db).sync_from_projects()
            print("Seed skipped: already have projects. Clients synced.")
            return
        projects = {item.name: ProjectService(db).create(item) for item in SEED_PROJECTS}
        TaskService(db).create(
            TaskCreate(
                title="Terminar generador NOM-019",
                project_id=projects["PROTEM"].id,
                status=TaskStatus.IN_PROGRESS,
                priority=Priority.URGENT,
            )
        )
        TaskService(db).create(
            TaskCreate(
                title="Carga masiva de productos",
                project_id=projects["Drop Universe"].id,
                status=TaskStatus.TODO,
                priority=Priority.HIGH,
            )
        )
        TaskService(db).create(
            TaskCreate(
                title="Seguimiento prospectos Condesa",
                project_id=projects["ENVOLVEX"].id,
                status=TaskStatus.TODO,
                priority=Priority.MEDIUM,
            )
        )
        IdeaService(db).create(
            IdeaCreate(
                title="Empaque para florerías",
                description="Línea de empaque premium para florerías.",
                project_id=projects["ENVOLVEX Packaging"].id,
                status=IdeaStatus.INBOX,
                impact=Impact.HIGH,
                effort=Effort.MEDIUM,
                source="seed",
            )
        )
        _seed_inbox(db, projects)
        _seed_files(db, projects)
        ClientService(db).sync_from_projects()
        print("Seed complete: 6 projects, 3 tasks, 1 idea, 3 inbox items, docs/access, clients.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
