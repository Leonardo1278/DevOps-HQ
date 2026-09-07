"""Clients and optional project.client_id.

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, Sequence[str], None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "clients",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=220), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_clients_slug", "clients", ["slug"], unique=True)
    op.create_index("ix_clients_status", "clients", ["status"])
    op.add_column("projects", sa.Column("client_id", sa.Uuid(), nullable=True))
    op.create_index("ix_projects_client_id", "projects", ["client_id"])
    op.create_foreign_key(
        "fk_projects_client_id",
        "projects",
        "clients",
        ["client_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_projects_client_id", "projects", type_="foreignkey")
    op.drop_index("ix_projects_client_id", table_name="projects")
    op.drop_column("projects", "client_id")
    op.drop_index("ix_clients_status", table_name="clients")
    op.drop_index("ix_clients_slug", table_name="clients")
    op.drop_table("clients")
