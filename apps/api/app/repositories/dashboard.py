from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.entities import Project, Task
from app.models.enums import Priority, ProjectHealth, ProjectStatus, TaskStatus

CLOSED_TASK_STATUSES = (TaskStatus.DONE.value, TaskStatus.CANCELED.value)
HIDDEN_PULSE_STATUSES = (ProjectStatus.ARCHIVED.value, ProjectStatus.DONE.value)


class DashboardRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def kpis(self) -> tuple[int, int, int]:
        pending = (
            self.db.scalar(
                select(func.count()).select_from(Task).where(Task.status.notin_(CLOSED_TASK_STATUSES))
            )
            or 0
        )
        urgent = (
            self.db.scalar(
                select(func.count())
                .select_from(Task)
                .where(
                    Task.status.notin_(CLOSED_TASK_STATUSES),
                    Task.priority == Priority.URGENT.value,
                )
            )
            or 0
        )
        active = (
            self.db.scalar(
                select(func.count())
                .select_from(Project)
                .where(Project.status == ProjectStatus.ACTIVE.value)
            )
            or 0
        )
        return pending, urgent, active

    def today_tasks(self, limit: int) -> list[Task]:
        priority_rank = case(
            (Task.priority == Priority.URGENT.value, 0),
            (Task.priority == Priority.HIGH.value, 1),
            (Task.priority == Priority.MEDIUM.value, 2),
            else_=3,
        )
        stmt = (
            select(Task)
            .options(selectinload(Task.project))
            .where(Task.status.notin_(CLOSED_TASK_STATUSES))
            .order_by(
                priority_rank,
                Task.due_at.asc().nulls_last(),
                Task.scheduled_at.asc().nulls_last(),
                Task.updated_at.desc(),
            )
            .limit(limit)
        )
        return list(self.db.scalars(stmt))

    def project_pulse(self, limit: int) -> list[Project]:
        health_rank = case(
            (Project.health == ProjectHealth.BLOCKED.value, 0),
            (Project.health == ProjectHealth.RISK.value, 1),
            (Project.health == ProjectHealth.WATCH.value, 2),
            else_=3,
        )
        stmt = (
            select(Project)
            .where(Project.status.notin_(HIDDEN_PULSE_STATUSES))
            .order_by(health_rank, Project.updated_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt))
