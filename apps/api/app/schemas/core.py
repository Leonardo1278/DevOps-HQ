from datetime import date, datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    ClientStatus,
    ConvertTarget,
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

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    status: ProjectStatus = ProjectStatus.PLANNING
    priority: Priority = Priority.MEDIUM
    health: ProjectHealth = ProjectHealth.WATCH
    progress_pct: int = Field(default=0, ge=0, le=100)
    color: str = Field(default="#3b82f6", max_length=16)
    icon: str = Field(default="", max_length=8)
    start_date: date | None = None
    target_date: date | None = None
    client_id: UUID | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: ProjectStatus | None = None
    priority: Priority | None = None
    health: ProjectHealth | None = None
    progress_pct: int | None = Field(default=None, ge=0, le=100)
    color: str | None = Field(default=None, max_length=16)
    icon: str | None = Field(default=None, max_length=8)
    start_date: date | None = None
    target_date: date | None = None
    client_id: UUID | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    description: str
    status: ProjectStatus
    priority: Priority
    health: ProjectHealth
    progress_pct: int
    color: str
    icon: str
    start_date: date | None
    target_date: date | None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    client_id: UUID | None = None


class ClientProjectRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    status: ProjectStatus
    color: str


class ClientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    notes: str = ""
    status: ClientStatus = ClientStatus.ACTIVE
    project_ids: list[UUID] = Field(default_factory=list)


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    notes: str | None = None
    status: ClientStatus | None = None
    project_ids: list[UUID] | None = None


class ClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    notes: str
    status: ClientStatus
    created_at: datetime
    updated_at: datetime
    projects: list[ClientProjectRef] = Field(default_factory=list)


class ChecklistItemIn(BaseModel):
    id: UUID | None = None
    title: str = Field(min_length=1, max_length=300)
    is_done: bool = False
    sort_order: int = 0


class ChecklistItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    is_done: bool
    sort_order: int


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str | None = None
    project_id: UUID | None = None
    status: TaskStatus = TaskStatus.TODO
    priority: Priority = Priority.MEDIUM
    due_at: datetime | None = None
    scheduled_at: datetime | None = None
    checklist: list[ChecklistItemIn] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = None
    project_id: UUID | None = None
    status: TaskStatus | None = None
    priority: Priority | None = None
    due_at: datetime | None = None
    scheduled_at: datetime | None = None
    checklist: list[ChecklistItemIn] | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID | None
    title: str
    description: str | None
    status: TaskStatus
    priority: Priority
    due_at: datetime | None
    scheduled_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    checklist_items: list[ChecklistItemOut] = Field(default_factory=list)


class IdeaCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str = ""
    project_id: UUID | None = None
    status: IdeaStatus = IdeaStatus.INBOX
    impact: Impact = Impact.MEDIUM
    effort: Effort = Effort.MEDIUM
    source: str = "manual"


class IdeaUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = None
    project_id: UUID | None = None
    status: IdeaStatus | None = None
    impact: Impact | None = None
    effort: Effort | None = None


class IdeaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID | None
    title: str
    description: str
    status: IdeaStatus
    impact: Impact
    effort: Effort
    score: int | None
    source: str
    converted_task_id: UUID | None
    created_at: datetime
    updated_at: datetime


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID | None
    entity_type: str
    entity_id: UUID | None
    action: str
    summary: str
    metadata_json: dict | None
    created_at: datetime


class InboxCreate(BaseModel):
    content: str = Field(min_length=1)
    item_type: InboxType = InboxType.UNKNOWN
    project_id: UUID | None = None


class InboxClassify(BaseModel):
    item_type: InboxType
    project_id: UUID | None = None


class InboxConvert(BaseModel):
    to: ConvertTarget
    project_id: UUID | None = None


class InboxOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    content: str
    item_type: InboxType
    processing_status: ProcessingStatus
    project_id: UUID | None
    converted_entity_type: str | None
    converted_entity_id: UUID | None
    created_at: datetime


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID | None
    title: str | None
    content: str
    created_at: datetime
    updated_at: datetime


class DashboardKpisOut(BaseModel):
    pending_tasks: int
    urgent_tasks: int
    active_projects: int
    receivable_amount: int | None = None


class DashboardProjectRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    color: str
    icon: str
    health: ProjectHealth
    progress_pct: int
    status: ProjectStatus


class DashboardTodayTask(BaseModel):
    id: UUID
    title: str
    priority: Priority
    status: TaskStatus
    due_at: datetime | None
    scheduled_at: datetime | None
    project: DashboardProjectRef | None = None


class DashboardOut(BaseModel):
    kpis: DashboardKpisOut
    today_tasks: list[DashboardTodayTask]
    project_pulse: list[DashboardProjectRef]
    recent_captures: list[InboxOut]
    recent_activity: list[ActivityOut]


class DocumentPresignIn(BaseModel):
    filename: str = Field(min_length=1, max_length=240)
    content_type: str = Field(default="application/octet-stream", max_length=200)


class DocumentPresignOut(BaseModel):
    upload_url: str
    method: str
    headers: dict[str, str]
    storage_key: str
    expires_in: int


class DocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str = ""
    project_id: UUID | None = None
    source_type: DocumentSource
    storage_key: str | None = None
    source_url: str | None = None
    content_type: str | None = Field(default=None, max_length=200)
    size_bytes: int | None = Field(default=None, ge=0)


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID | None
    title: str
    description: str
    source_type: DocumentSource
    storage_key: str | None
    source_url: str | None
    content_type: str | None
    size_bytes: int | None
    created_at: datetime
    updated_at: datetime


class DocumentUrlOut(BaseModel):
    url: str
    source_type: DocumentSource


class CredentialCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    kind: CredentialKind = CredentialKind.OTHER
    secret_ref: str = Field(min_length=1, max_length=500)
    project_id: UUID | None = None
    notes: str = ""


class CredentialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID | None
    name: str
    kind: CredentialKind
    secret_ref: str
    notes: str
    created_at: datetime

