"""add cluster_id to users

Revision ID: h7j5e6f8g9i0
Revises: g6i4d5e7f8h9
Create Date: 2026-04-19 10:00:00.000000

Changes:
  - ALTER TABLE users ADD COLUMN cluster_id (integer, nullable)
  - Allows grouping users into clusters via K-Means so the collaborative
    recommender can compare each user only against similar users.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'h7j5e6f8g9i0'
down_revision: Union[str, Sequence[str], None] = 'g6i4d5e7f8h9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add cluster_id column. Nullable so existing users (without clustering
    # run yet) are allowed to exist.
    op.add_column(
        'users',
        sa.Column('cluster_id', sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('users', 'cluster_id')
