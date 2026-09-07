from sqlalchemy.orm import Session

from app.repositories.core import ActivityRepository, InboxRepository
from app.repositories.dashboard import DashboardRepository
from app.schemas.core import (
    ActivityOut,
    DashboardKpisOut,
    DashboardOut,
    DashboardProjectRef,
    DashboardTodayTask,
    InboxOut,
)

TODAY_LIMIT = 5
PULSE_LIMIT = 8
CAPTURES_LIMIT = 5
ACTIVITY_LIMIT = 6


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.repo = DashboardRepository(db)
        self.inbox = InboxRepository(db)
        self.activity = ActivityRepository(db)

    def get(self) -> DashboardOut:
        pending, urgent, active = self.repo.kpis()
        today = self.repo.today_tasks(TODAY_LIMIT)
        pulse = self.repo.project_pulse(PULSE_LIMIT)
        captures, _ = self.inbox.list(
            project_id=None,
            item_type=None,
            include_converted=False,
            q=None,
            limit=CAPTURES_LIMIT,
            offset=0,
        )
        events, _ = self.activity.list(project_id=None, limit=ACTIVITY_LIMIT, offset=0)
        return DashboardOut(
            kpis=DashboardKpisOut(
                pending_tasks=pending,
                urgent_tasks=urgent,
                active_projects=active,
                receivable_amount=None,
            ),
            today_tasks=[
                DashboardTodayTask(
                    id=task.id,
                    title=task.title,
                    priority=task.priority,
                    status=task.status,
                    due_at=task.due_at,
                    scheduled_at=task.scheduled_at,
                    project=DashboardProjectRef.model_validate(task.project) if task.project else None,
                )
                for task in today
            ],
            project_pulse=[DashboardProjectRef.model_validate(project) for project in pulse],
            recent_captures=[InboxOut.model_validate(item) for item in captures],
            recent_activity=[ActivityOut.model_validate(event) for event in events],
        )
