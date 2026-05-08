"""add is_bookmarked to user_learning_resources and is_skipped

Revision ID: L2o0k1l3m4n5
Revises: k1n9j0k2l3m4
Create Date: 2026-05-08 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "L2o0k1l3m4n5"
down_revision: Union[str, None] = "k1n9j0k2l3m4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Bookmark flag on the interaction row
    op.add_column(
        "user_learning_resources",
        sa.Column("is_bookmarked", sa.Boolean(), nullable=False, server_default="false"),
    )
    # Track resources the user explicitly skipped ("see another")
    op.add_column(
        "user_learning_resources",
        sa.Column("is_skipped", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("user_learning_resources", "is_skipped")
    op.drop_column("user_learning_resources", "is_bookmarked")