from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utcnow
from app.db.base import Base
from app.models.enums import (
    ClientStatus,
    CredentialKind,
    DocumentSource,
    Effort,
    IdeaStatus,
    Impact,
    InboxType,
    Priority,
    ProcessingStatus,
    ProjectHealth,
    ProjectStatus,
    TaskStatus,
)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(220), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(
        String(32), default=ProjectStatus.PLANNING.value, index=True
    )
    priority: Mapped[str] = mapped_column(String(32), default=Priority.MEDIUM.value)
    health: Mapped[str] = mapped_column(String(32), default=ProjectHealth.WATCH.value)
    progress_pct: Mapped[int] = mapped_column(Integer, default=0)
    color: Mapped[str] = mapped_column(String(16), default="#3b82f6")
    icon: Mapped[str] = mapped_column(String(8), default="")
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    client_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True
    )

    client: Mapped[Client | None] = relationship(back_populates="projects")
    tasks: Mapped[list[Task]] = relationship(back_populates="project")
    ideas: Mapped[list[Idea]] = relationship(back_populates="project")


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(220), unique=True, index=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(
        String(32), default=ClientStatus.ACTIVE.value, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    projects: Mapped[list[Project]] = relationship(back_populates="client")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=TaskStatus.TODO.value, index=True)
    priority: Mapped[str] = mapped_column(String(32), default=Priority.MEDIUM.value, index=True)
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    project: Mapped[Project | None] = relationship(back_populates="tasks")
    checklist_items: Mapped[list[TaskChecklistItem]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskChecklistItem.sort_order",
    )


class TaskChecklistItem(Base):
    __tablename__ = "task_checklist_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tasks.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(300))
    is_done: Mapped[bool] = mapped_column(default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    task: Mapped[Task] = relationship(back_populates="checklist_items")


class Idea(Base):
    __tablename__ = "ideas"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default=IdeaStatus.INBOX.value, index=True)
    impact: Mapped[str] = mapped_column(String(32), default=Impact.MEDIUM.value)
    effort: Mapped[str] = mapped_column(String(32), default=Effort.MEDIUM.value)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(String(80), default="manual")
    converted_task_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    project: Mapped[Project | None] = relationship(back_populates="ideas")


class InboxItem(Base):
    __tablename__ = "inbox_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    content: Mapped[str] = mapped_column(Text)
    item_type: Mapped[str] = mapped_column(
        String(32), default=InboxType.UNKNOWN.value, index=True
    )
    processing_status: Mapped[str] = mapped_column(
        String(32), default=ProcessingStatus.PENDING.value, index=True
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    converted_entity_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    converted_entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )

    project: Mapped[Project | None] = relationship()


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    project: Mapped[Project | None] = relationship()


class ActivityEvent(Base):
    __tablename__ = "activity_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    entity_type: Mapped[str] = mapped_column(String(32), index=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    action: Mapped[str] = mapped_column(String(32))
    summary: Mapped[str] = mapped_column(String(500))
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    source_type: Mapped[str] = mapped_column(
        String(16), default=DocumentSource.URL.value, index=True
    )
    storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(200), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    project: Mapped[Project | None] = relationship()


class CredentialRef(Base):
    __tablename__ = "credential_refs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(
        String(32), default=CredentialKind.OTHER.value, index=True
    )
    secret_ref: Mapped[str] = mapped_column(String(500))
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    project: Mapped[Project | None] = relationship()
