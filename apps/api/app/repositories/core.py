from __future__ import annotations

import uuid

from sqlalchemy import Select, case, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.entities import ActivityEvent, Idea, InboxItem, Note, Project, Task, TaskChecklistItem
from app.models.enums import ProjectStatus

PROJECT_SORTS = ("updated", "name", "active_first", "planning_first")


def _project_order(sort: str):
    if sort == "name":
        return (Project.name.asc(),)
    if sort == "active_first":
        return (
            case(
                (Project.status == ProjectStatus.ACTIVE.value, 0),
                (Project.status == ProjectStatus.PLANNING.value, 1),
                (Project.status == ProjectStatus.PAUSED.value, 2),
                (Project.status == ProjectStatus.DONE.value, 3),
                else_=4,
            ),
            Project.name.asc(),
        )
    if sort == "planning_first":
        return (
            case(
                (Project.status == ProjectStatus.PLANNING.value, 0),
                (Project.status == ProjectStatus.PAUSED.value, 1),
                (Project.status == ProjectStatus.ACTIVE.value, 2),
                (Project.status == ProjectStatus.DONE.value, 3),
                else_=4,
            ),
            Project.name.asc(),
        )
    return (Project.updated_at.desc(),)


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, project_id: uuid.UUID) -> Project | None:
        return self.db.get(Project, project_id)

    def get_by_slug(self, slug: str) -> Project | None:
        return self.db.scalar(select(Project).where(Project.slug == slug))

    def list(
        self,
        *,
        status: str | None,
        priority: str | None,
        q: str | None,
        include_archived: bool,
        sort: str,
        limit: int,
        offset: int,
    ) -> tuple[list[Project], int]:
        stmt: Select[tuple[Project]] = select(Project)
        count_stmt: Select[tuple[int]] = select(func.count()).select_from(Project)
        if status:
            stmt = stmt.where(Project.status == status)
            count_stmt = count_stmt.where(Project.status == status)
        elif not include_archived:
            stmt = stmt.where(Project.status != ProjectStatus.ARCHIVED.value)
            count_stmt = count_stmt.where(Project.status != ProjectStatus.ARCHIVED.value)
        if priority:
            stmt = stmt.where(Project.priority == priority)
            count_stmt = count_stmt.where(Project.priority == priority)
        if q:
            pattern = f"%{q}%"
            filt = or_(Project.name.ilike(pattern), Project.description.ilike(pattern))
            stmt = stmt.where(filt)
            count_stmt = count_stmt.where(filt)
        total = self.db.scalar(count_stmt) or 0
        items = list(
            self.db.scalars(stmt.order_by(*_project_order(sort)).limit(limit).offset(offset))
        )
        return items, total

    def add(self, project: Project) -> Project:
        self.db.add(project)
        self.db.flush()
        return project

    def delete(self, project: Project) -> None:
        self.db.delete(project)


class TaskRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, task_id: uuid.UUID) -> Task | None:
        return self.db.scalar(
            select(Task)
            .options(selectinload(Task.checklist_items))
            .where(Task.id == task_id)
        )

    def list(
        self,
        *,
        project_id: uuid.UUID | None,
        status: str | None,
        priority: str | None,
        q: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Task], int]:
        stmt = select(Task).options(selectinload(Task.checklist_items))
        count_stmt = select(func.count()).select_from(Task)
        if project_id:
            stmt = stmt.where(Task.project_id == project_id)
            count_stmt = count_stmt.where(Task.project_id == project_id)
        if status:
            stmt = stmt.where(Task.status == status)
            count_stmt = count_stmt.where(Task.status == status)
        if priority:
            stmt = stmt.where(Task.priority == priority)
            count_stmt = count_stmt.where(Task.priority == priority)
        if q:
            pattern = f"%{q}%"
            filt = or_(Task.title.ilike(pattern), Task.description.ilike(pattern))
            stmt = stmt.where(filt)
            count_stmt = count_stmt.where(filt)
        total = self.db.scalar(count_stmt) or 0
        items = list(
            self.db.scalars(
                stmt.order_by(Task.due_at.asc().nulls_last(), Task.updated_at.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        return items, total

    def add(self, task: Task) -> Task:
        self.db.add(task)
        self.db.flush()
        return task

    def delete(self, task: Task) -> None:
        self.db.delete(task)

    def replace_checklist(self, task: Task, items: list[TaskChecklistItem]) -> None:
        task.checklist_items.clear()
        self.db.flush()
        for item in items:
            task.checklist_items.append(item)
        self.db.flush()


class IdeaRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, idea_id: uuid.UUID) -> Idea | None:
        return self.db.get(Idea, idea_id)

    def list(
        self,
        *,
        project_id: uuid.UUID | None,
        status: str | None,
        q: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Idea], int]:
        stmt = select(Idea)
        count_stmt = select(func.count()).select_from(Idea)
        if project_id:
            stmt = stmt.where(Idea.project_id == project_id)
            count_stmt = count_stmt.where(Idea.project_id == project_id)
        if status:
            stmt = stmt.where(Idea.status == status)
            count_stmt = count_stmt.where(Idea.status == status)
        if q:
            pattern = f"%{q}%"
            filt = or_(Idea.title.ilike(pattern), Idea.description.ilike(pattern))
            stmt = stmt.where(filt)
            count_stmt = count_stmt.where(filt)
        total = self.db.scalar(count_stmt) or 0
        items = list(
            self.db.scalars(stmt.order_by(Idea.updated_at.desc()).limit(limit).offset(offset))
        )
        return items, total

    def add(self, idea: Idea) -> Idea:
        self.db.add(idea)
        self.db.flush()
        return idea

    def delete(self, idea: Idea) -> None:
        self.db.delete(idea)


class ActivityRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, event: ActivityEvent) -> ActivityEvent:
        self.db.add(event)
        self.db.flush()
        return event

    def list(
        self,
        *,
        project_id: uuid.UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[list[ActivityEvent], int]:
        stmt = select(ActivityEvent)
        count_stmt = select(func.count()).select_from(ActivityEvent)
        if project_id:
            stmt = stmt.where(ActivityEvent.project_id == project_id)
            count_stmt = count_stmt.where(ActivityEvent.project_id == project_id)
        total = self.db.scalar(count_stmt) or 0
        items = list(
            self.db.scalars(
                stmt.order_by(ActivityEvent.created_at.desc()).limit(limit).offset(offset)
            )
        )
        return items, total


class InboxRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, item_id: uuid.UUID) -> InboxItem | None:
        return self.db.get(InboxItem, item_id)

    def list(
        self,
        *,
        project_id: uuid.UUID | None,
        item_type: str | None,
        include_converted: bool,
        q: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[InboxItem], int]:
        stmt = select(InboxItem)
        count_stmt = select(func.count()).select_from(InboxItem)
        if project_id:
            stmt = stmt.where(InboxItem.project_id == project_id)
            count_stmt = count_stmt.where(InboxItem.project_id == project_id)
        if item_type:
            stmt = stmt.where(InboxItem.item_type == item_type)
            count_stmt = count_stmt.where(InboxItem.item_type == item_type)
        if not include_converted:
            stmt = stmt.where(InboxItem.processing_status != "CONVERTED")
            count_stmt = count_stmt.where(InboxItem.processing_status != "CONVERTED")
        if q:
            pattern = f"%{q}%"
            stmt = stmt.where(InboxItem.content.ilike(pattern))
            count_stmt = count_stmt.where(InboxItem.content.ilike(pattern))
        total = self.db.scalar(count_stmt) or 0
        items = list(
            self.db.scalars(
                stmt.order_by(InboxItem.created_at.desc()).limit(limit).offset(offset)
            )
        )
        return items, total

    def add(self, item: InboxItem) -> InboxItem:
        self.db.add(item)
        self.db.flush()
        return item


class NoteRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, note_id: uuid.UUID) -> Note | None:
        return self.db.get(Note, note_id)

    def add(self, note: Note) -> Note:
        self.db.add(note)
        self.db.flush()
        return note

