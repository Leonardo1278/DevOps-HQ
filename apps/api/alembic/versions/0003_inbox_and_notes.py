"""Inbox items and notes (embeddings deferred to phase 6).

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-31
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, Sequence[str], None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=300), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notes_project_id", "notes", ["project_id"])

    op.create_table(
        "inbox_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("item_type", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
        sa.Column(
            "processing_status",
            sa.String(length=32),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("converted_entity_type", sa.String(length=32), nullable=True),
        sa.Column("converted_entity_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inbox_items_item_type", "inbox_items", ["item_type"])
    op.create_index(
        "ix_inbox_items_processing_status", "inbox_items", ["processing_status"]
    )
    op.create_index("ix_inbox_items_project_id", "inbox_items", ["project_id"])
    op.create_index("ix_inbox_items_created_at", "inbox_items", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_inbox_items_created_at", table_name="inbox_items")
    op.drop_index("ix_inbox_items_project_id", table_name="inbox_items")
    op.drop_index("ix_inbox_items_processing_status", table_name="inbox_items")
    op.drop_index("ix_inbox_items_item_type", table_name="inbox_items")
    op.drop_table("inbox_items")
    op.drop_index("ix_notes_project_id", table_name="notes")
    op.drop_table("notes")
