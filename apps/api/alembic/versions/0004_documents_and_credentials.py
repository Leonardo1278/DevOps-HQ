"""Documents metadata and credential_refs (no secrets, no blobs).

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-31
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, Sequence[str], None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("source_type", sa.String(length=16), nullable=False, server_default="URL"),
        sa.Column("storage_key", sa.String(length=500), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("content_type", sa.String(length=200), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_documents_project_id", "documents", ["project_id"])
    op.create_index("ix_documents_source_type", "documents", ["source_type"])

    op.create_table(
        "credential_refs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False, server_default="OTHER"),
        sa.Column("secret_ref", sa.String(length=500), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_credential_refs_project_id", "credential_refs", ["project_id"])
    op.create_index("ix_credential_refs_kind", "credential_refs", ["kind"])


def downgrade() -> None:
    op.drop_index("ix_credential_refs_kind", table_name="credential_refs")
    op.drop_index("ix_credential_refs_project_id", table_name="credential_refs")
    op.drop_table("credential_refs")
    op.drop_index("ix_documents_source_type", table_name="documents")
    op.drop_index("ix_documents_project_id", table_name="documents")
    op.drop_table("documents")
