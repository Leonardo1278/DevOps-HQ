"""Core entities: projects, tasks, ideas, activity.

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-31
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=220), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PLANNING"),
        sa.Column("priority", sa.String(length=32), nullable=False, server_default="MEDIUM"),
        sa.Column("health", sa.String(length=32), nullable=False, server_default="WATCH"),
        sa.Column("progress_pct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("color", sa.String(length=16), nullable=False, server_default="#3b82f6"),
        sa.Column("icon", sa.String(length=8), nullable=False, server_default=""),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_projects_slug", "projects", ["slug"], unique=True)
    op.create_index("ix_projects_status", "projects", ["status"])

    op.create_table(
        "tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="TODO"),
        sa.Column("priority", sa.String(length=32), nullable=False, server_default="MEDIUM"),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tasks_project_id", "tasks", ["project_id"])
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_priority", "tasks", ["priority"])
    op.create_index("ix_tasks_due_at", "tasks", ["due_at"])

    op.create_table(
        "task_checklist_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("is_done", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_task_checklist_items_task_id", "task_checklist_items", ["task_id"])

    op.create_table(
        "ideas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="INBOX"),
        sa.Column("impact", sa.String(length=32), nullable=False, server_default="MEDIUM"),
        sa.Column("effort", sa.String(length=32), nullable=False, server_default="MEDIUM"),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(length=80), nullable=False, server_default="manual"),
        sa.Column("converted_task_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["converted_task_id"], ["tasks.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ideas_project_id", "ideas", ["project_id"])
    op.create_index("ix_ideas_status", "ideas", ["status"])

    op.create_table(
        "activity_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_activity_events_project_id", "activity_events", ["project_id"])
    op.create_index("ix_activity_events_entity_type", "activity_events", ["entity_type"])
    op.create_index("ix_activity_events_created_at", "activity_events", ["created_at"])


def downgrade() -> None:
    op.drop_table("activity_events")
    op.drop_table("ideas")
    op.drop_table("task_checklist_items")
    op.drop_table("tasks")
    op.drop_table("projects")
