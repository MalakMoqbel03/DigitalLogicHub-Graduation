"""add is_bookmarked to user_learning_resources and is_skipped

Revision ID: M3p1l2m4n5o6
Revises: k1n9j0k2l3m4
Create Date: 2026-05-08 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "M3p1l2m4n5o6"
down_revision: Union[str, None] = "k1n9j0k2l3m4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_learning_resources",
        sa.Column("is_bookmarked", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "user_learning_resources",
        sa.Column("is_skipped", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("user_learning_resources", "is_skipped")
    op.drop_column("user_learning_resources", "is_bookmarked")
