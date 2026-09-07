from __future__ import annotations

import re
import unicodedata
import uuid

from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models.entities import ActivityEvent, Idea, InboxItem, Note, Project, Task, TaskChecklistItem
from app.models.enums import (
    ActivityAction,
    ConvertTarget,
    IdeaStatus,
    InboxType,
    Priority,
    ProcessingStatus,
    ProjectStatus,
    TaskStatus,
)
from app.repositories.core import (
    ActivityRepository,
    IdeaRepository,
    InboxRepository,
    NoteRepository,
    ProjectRepository,
    TaskRepository,
)
from app.schemas.core import (
    ChecklistItemIn,
    IdeaCreate,
    IdeaUpdate,
    InboxClassify,
    InboxConvert,
    InboxCreate,
    ProjectCreate,
    ProjectUpdate,
    TaskCreate,
    TaskUpdate,
)


class NotFoundError(Exception):
    def __init__(self, entity: str, entity_id: uuid.UUID) -> None:
        super().__init__(f"{entity} {entity_id} not found")
        self.entity = entity
        self.entity_id = entity_id


class ConflictError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


def split_capture(content: str) -> tuple[str, str]:
    lines = [line.strip() for line in content.strip().splitlines() if line.strip()]
    title = (lines[0] if lines else content.strip())[:300]
    rest = "\n".join(lines[1:]).strip()
    return title, rest


def capture_preview(content: str, limit: int = 80) -> str:
    compact = " ".join(content.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 1]}…"


def slugify(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return slug or "project"


def unique_slug(repo: ProjectRepository, name: str, exclude_id: uuid.UUID | None = None) -> str:
    base = slugify(name)
    candidate = base
    suffix = 2
    while True:
        existing = repo.get_by_slug(candidate)
        if existing is None or existing.id == exclude_id:
            return candidate
        candidate = f"{base}-{suffix}"
        suffix += 1


def record_activity(
    db: Session,
    *,
    action: ActivityAction,
    entity_type: str,
    entity_id: uuid.UUID | None,
    summary: str,
    project_id: uuid.UUID | None = None,
    metadata: dict | None = None,
) -> None:
    ActivityRepository(db).add(
        ActivityEvent(
            project_id=project_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action.value,
            summary=summary,
            metadata_json=metadata,
        )
    )


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProjectRepository(db)

    def get(self, project_id: uuid.UUID) -> Project:
        project = self.repo.get(project_id)
        if project is None:
            raise NotFoundError("project", project_id)
        return project

    def list(self, **kwargs):  # noqa: ANN003
        return self.repo.list(**kwargs)

    def _ensure_client(self, client_id: uuid.UUID | None) -> None:
        if client_id is None:
            return
        from app.services.clients import ClientService

        ClientService(self.db).get(client_id)

    def create(self, payload: ProjectCreate) -> Project:
        self._ensure_client(payload.client_id)
        project = Project(
            name=payload.name.strip(),
            slug=unique_slug(self.repo, payload.name),
            description=payload.description,
            status=payload.status.value,
            priority=payload.priority.value,
            health=payload.health.value,
            progress_pct=payload.progress_pct,
            color=payload.color,
            icon=payload.icon or payload.name.strip()[:2].upper(),
            start_date=payload.start_date,
            target_date=payload.target_date,
            client_id=payload.client_id,
        )
        self.repo.add(project)
        record_activity(
            self.db,
            action=ActivityAction.CREATED,
            entity_type="project",
            entity_id=project.id,
            project_id=project.id,
            summary=f"Proyecto creado · {project.name}",
        )
        self.db.commit()
        self.db.refresh(project)
        return project

    def update(self, project_id: uuid.UUID, payload: ProjectUpdate) -> Project:
        project = self.get(project_id)
        data = payload.model_dump(exclude_unset=True)
        if "client_id" in data:
            self._ensure_client(data["client_id"])
        if "name" in data and data["name"] is not None:
            new_name = data["name"].strip()
            if new_name != project.name:
                project.name = new_name
                project.slug = unique_slug(self.repo, new_name, exclude_id=project.id)
        for field in (
            "description",
            "progress_pct",
            "color",
            "icon",
            "start_date",
            "target_date",
            "client_id",
        ):
            if field in data:
                setattr(project, field, data[field])
        for field in ("status", "priority", "health"):
            if field in data and data[field] is not None:
                setattr(project, field, data[field].value)
        if project.status == ProjectStatus.ARCHIVED.value:
            if project.archived_at is None:
                project.archived_at = utcnow()
        else:
            project.archived_at = None
        project.updated_at = utcnow()
        record_activity(
            self.db,
            action=ActivityAction.UPDATED,
            entity_type="project",
            entity_id=project.id,
            project_id=project.id,
            summary=f"Proyecto actualizado · {project.name}",
        )
        self.db.commit()
        self.db.refresh(project)
        return project

    def archive(self, project_id: uuid.UUID) -> Project:
        project = self.get(project_id)
        project.status = ProjectStatus.ARCHIVED.value
        project.archived_at = utcnow()
        project.updated_at = utcnow()
        record_activity(
            self.db,
            action=ActivityAction.ARCHIVED,
            entity_type="project",
            entity_id=project.id,
            project_id=project.id,
            summary=f"Proyecto archivado · {project.name}",
        )
        self.db.commit()
        self.db.refresh(project)
        return project

    def purge(self, project_id: uuid.UUID) -> None:
        project = self.get(project_id)
        record_activity(
            self.db,
            action=ActivityAction.DELETED,
            entity_type="project",
            entity_id=project.id,
            project_id=None,
            summary=f"Proyecto borrado · {project.name}",
        )
        self.repo.delete(project)
        self.db.commit()


def _checklist_from_payload(items: list[ChecklistItemIn]) -> list[TaskChecklistItem]:
    return [
        TaskChecklistItem(
            id=item.id or uuid.uuid4(),
            title=item.title,
            is_done=item.is_done,
            sort_order=item.sort_order or index,
        )
        for index, item in enumerate(items)
    ]


class TaskService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = TaskRepository(db)

    def get(self, task_id: uuid.UUID) -> Task:
        task = self.repo.get(task_id)
        if task is None:
            raise NotFoundError("task", task_id)
        return task

    def list(self, **kwargs):  # noqa: ANN003
        return self.repo.list(**kwargs)

    def create(self, payload: TaskCreate) -> Task:
        if payload.project_id:
            ProjectService(self.db).get(payload.project_id)
        task = Task(
            title=payload.title.strip(),
            description=payload.description,
            project_id=payload.project_id,
            status=payload.status.value,
            priority=payload.priority.value,
            due_at=payload.due_at,
            scheduled_at=payload.scheduled_at,
        )
        if payload.status == TaskStatus.DONE:
            task.completed_at = utcnow()
        task.checklist_items = _checklist_from_payload(payload.checklist)
        self.repo.add(task)
        record_activity(
            self.db,
            action=ActivityAction.CREATED,
            entity_type="task",
            entity_id=task.id,
            project_id=task.project_id,
            summary=f"Tarea creada · {task.title}",
        )
        self.db.commit()
        return self.get(task.id)

    def update(self, task_id: uuid.UUID, payload: TaskUpdate) -> Task:
        task = self.get(task_id)
        data = payload.model_dump(exclude_unset=True)
        if "project_id" in data and data["project_id"]:
            ProjectService(self.db).get(data["project_id"])
        if "title" in data and data["title"] is not None:
            task.title = data["title"].strip()
        for field in ("description", "project_id", "due_at", "scheduled_at"):
            if field in data:
                setattr(task, field, data[field])
        if "status" in data and data["status"] is not None:
            task.status = data["status"].value
            if data["status"] == TaskStatus.DONE and task.completed_at is None:
                task.completed_at = utcnow()
            if data["status"] != TaskStatus.DONE:
                task.completed_at = None
        if "priority" in data and data["priority"] is not None:
            task.priority = data["priority"].value
        if payload.checklist is not None:
            self.repo.replace_checklist(task, _checklist_from_payload(payload.checklist))
        task.updated_at = utcnow()
        record_activity(
            self.db,
            action=ActivityAction.UPDATED,
            entity_type="task",
            entity_id=task.id,
            project_id=task.project_id,
            summary=f"Tarea actualizada · {task.title}",
        )
        self.db.commit()
        return self.get(task.id)

    def complete(self, task_id: uuid.UUID) -> Task:
        task = self.get(task_id)
        task.status = TaskStatus.DONE.value
        task.completed_at = utcnow()
        task.updated_at = utcnow()
        record_activity(
            self.db,
            action=ActivityAction.COMPLETED,
            entity_type="task",
            entity_id=task.id,
            project_id=task.project_id,
            summary=f"Tarea completada · {task.title}",
        )
        self.db.commit()
        return self.get(task.id)

    def delete(self, task_id: uuid.UUID) -> None:
        task = self.get(task_id)
        record_activity(
            self.db,
            action=ActivityAction.DELETED,
            entity_type="task",
            entity_id=task.id,
            project_id=task.project_id,
            summary=f"Tarea borrada · {task.title}",
        )
        self.repo.delete(task)
        self.db.commit()


class IdeaService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = IdeaRepository(db)

    def get(self, idea_id: uuid.UUID) -> Idea:
        idea = self.repo.get(idea_id)
        if idea is None:
            raise NotFoundError("idea", idea_id)
        return idea

    def list(self, **kwargs):  # noqa: ANN003
        return self.repo.list(**kwargs)

    def create(self, payload: IdeaCreate) -> Idea:
        if payload.project_id:
            ProjectService(self.db).get(payload.project_id)
        idea = Idea(
            title=payload.title.strip(),
            description=payload.description,
            project_id=payload.project_id,
            status=payload.status.value,
            impact=payload.impact.value,
            effort=payload.effort.value,
            source=payload.source,
        )
        self.repo.add(idea)
        record_activity(
            self.db,
            action=ActivityAction.CREATED,
            entity_type="idea",
            entity_id=idea.id,
            project_id=idea.project_id,
            summary=f"Idea creada · {idea.title}",
        )
        self.db.commit()
        self.db.refresh(idea)
        return idea

    def update(self, idea_id: uuid.UUID, payload: IdeaUpdate) -> Idea:
        idea = self.get(idea_id)
        data = payload.model_dump(exclude_unset=True)
        if "project_id" in data and data["project_id"]:
            ProjectService(self.db).get(data["project_id"])
        if "title" in data and data["title"] is not None:
            idea.title = data["title"].strip()
        for field in ("description", "project_id"):
            if field in data:
                setattr(idea, field, data[field])
        for field in ("status", "impact", "effort"):
            if field in data and data[field] is not None:
                setattr(idea, field, data[field].value)
        idea.updated_at = utcnow()
        record_activity(
            self.db,
            action=ActivityAction.UPDATED,
            entity_type="idea",
            entity_id=idea.id,
            project_id=idea.project_id,
            summary=f"Idea actualizada · {idea.title}",
        )
        self.db.commit()
        self.db.refresh(idea)
        return idea

    def convert_to_task(self, idea_id: uuid.UUID) -> tuple[Idea, Task]:
        idea = self.get(idea_id)
        if idea.status == IdeaStatus.CONVERTED.value and idea.converted_task_id:
            task = TaskService(self.db).get(idea.converted_task_id)
            return idea, task
        task = TaskService(self.db).create(
            TaskCreate(
                title=idea.title,
                description=idea.description or None,
                project_id=idea.project_id,
                status=TaskStatus.TODO,
                priority=Priority.MEDIUM,
            )
        )
        idea.status = IdeaStatus.CONVERTED.value
        idea.converted_task_id = task.id
        idea.updated_at = utcnow()
        record_activity(
            self.db,
            action=ActivityAction.CONVERTED,
            entity_type="idea",
            entity_id=idea.id,
            project_id=idea.project_id,
            summary=f"Idea convertida a tarea · {idea.title}",
            metadata={"task_id": str(task.id), "idea_id": str(idea.id)},
        )
        self.db.commit()
        self.db.refresh(idea)
        return idea, TaskService(self.db).get(task.id)

    def delete(self, idea_id: uuid.UUID) -> None:
        idea = self.get(idea_id)
        record_activity(
            self.db,
            action=ActivityAction.DELETED,
            entity_type="idea",
            entity_id=idea.id,
            project_id=idea.project_id,
            summary=f"Idea borrada · {idea.title}",
        )
        self.repo.delete(idea)
        self.db.commit()


class ActivityService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ActivityRepository(db)

    def list(self, **kwargs):  # noqa: ANN003
        return self.repo.list(**kwargs)


class NoteService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = NoteRepository(db)

    def get(self, note_id: uuid.UUID) -> Note:
        note = self.repo.get(note_id)
        if note is None:
            raise NotFoundError("note", note_id)
        return note

    def create(self, *, title: str | None, content: str, project_id: uuid.UUID | None) -> Note:
        if project_id:
            ProjectService(self.db).get(project_id)
        note = Note(title=title, content=content, project_id=project_id)
        self.repo.add(note)
        record_activity(
            self.db,
            action=ActivityAction.CREATED,
            entity_type="note",
            entity_id=note.id,
            project_id=project_id,
            summary=f"Nota creada · {title or capture_preview(content)}",
        )
        self.db.commit()
        self.db.refresh(note)
        return note


class InboxService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = InboxRepository(db)

    def get(self, item_id: uuid.UUID) -> InboxItem:
        item = self.repo.get(item_id)
        if item is None:
            raise NotFoundError("inbox", item_id)
        return item

    def list(self, **kwargs):  # noqa: ANN003
        return self.repo.list(**kwargs)

    def create(self, payload: InboxCreate) -> InboxItem:
        if payload.project_id:
            ProjectService(self.db).get(payload.project_id)
        status = (
            ProcessingStatus.CLASSIFIED
            if payload.item_type != InboxType.UNKNOWN
            else ProcessingStatus.PENDING
        )
        item = InboxItem(
            content=payload.content.strip(),
            item_type=payload.item_type.value,
            processing_status=status.value,
            project_id=payload.project_id,
        )
        self.repo.add(item)
        record_activity(
            self.db,
            action=ActivityAction.CREATED,
            entity_type="inbox",
            entity_id=item.id,
            project_id=item.project_id,
            summary=f"Captura · {capture_preview(item.content)}",
        )
        self.db.commit()
        self.db.refresh(item)
        return item

    def classify(self, item_id: uuid.UUID, payload: InboxClassify) -> InboxItem:
        item = self.get(item_id)
        if item.processing_status == ProcessingStatus.CONVERTED.value:
            raise ConflictError("Esta captura ya fue convertida")
        if payload.project_id:
            ProjectService(self.db).get(payload.project_id)
            item.project_id = payload.project_id
        item.item_type = payload.item_type.value
        item.processing_status = (
            ProcessingStatus.PENDING.value
            if payload.item_type == InboxType.UNKNOWN
            else ProcessingStatus.CLASSIFIED.value
        )
        record_activity(
            self.db,
            action=ActivityAction.CLASSIFIED,
            entity_type="inbox",
            entity_id=item.id,
            project_id=item.project_id,
            summary=f"Captura clasificada · {payload.item_type.value}",
        )
        self.db.commit()
        self.db.refresh(item)
        return item

    def convert(self, item_id: uuid.UUID, payload: InboxConvert) -> InboxItem:
        item = self.get(item_id)
        if item.processing_status == ProcessingStatus.CONVERTED.value:
            raise ConflictError("Esta captura ya fue convertida")
        project_id = payload.project_id or item.project_id
        if project_id:
            ProjectService(self.db).get(project_id)
        title, rest = split_capture(item.content)
        entity_type: str
        entity_id: uuid.UUID
        if payload.to == ConvertTarget.TASK:
            task = TaskService(self.db).create(
                TaskCreate(
                    title=title,
                    description=rest or None,
                    project_id=project_id,
                    status=TaskStatus.TODO,
                    priority=Priority.MEDIUM,
                )
            )
            entity_type, entity_id = "task", task.id
            if item.item_type == InboxType.UNKNOWN.value:
                item.item_type = InboxType.TASK.value
        elif payload.to == ConvertTarget.IDEA:
            idea = IdeaService(self.db).create(
                IdeaCreate(
                    title=title,
                    description=rest,
                    project_id=project_id,
                    source="inbox",
                )
            )
            entity_type, entity_id = "idea", idea.id
            if item.item_type == InboxType.UNKNOWN.value:
                item.item_type = InboxType.IDEA.value
        else:
            note = NoteService(self.db).create(
                title=title,
                content=item.content.strip(),
                project_id=project_id,
            )
            entity_type, entity_id = "note", note.id
            if item.item_type == InboxType.UNKNOWN.value:
                item.item_type = InboxType.NOTE.value
        item.converted_entity_type = entity_type
        item.converted_entity_id = entity_id
        item.processing_status = ProcessingStatus.CONVERTED.value
        record_activity(
            self.db,
            action=ActivityAction.CONVERTED,
            entity_type="inbox",
            entity_id=item.id,
            project_id=project_id,
            summary=f"Captura convertida a {entity_type} · {title}",
            metadata={"target": entity_type, "entity_id": str(entity_id)},
        )
        self.db.commit()
        self.db.refresh(item)
        return item
