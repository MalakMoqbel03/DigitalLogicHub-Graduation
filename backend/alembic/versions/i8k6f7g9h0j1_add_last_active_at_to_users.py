"""add last_active_at to users

Revision ID: i8k6f7g9h0j1
Revises: h7j5e6f8g9i0
Create Date: 2026-05-05 12:00:00.000000

Changes:
  - ALTER TABLE users ADD COLUMN last_active_at (timestamp, nullable)
  - Required by hybrid.py _context_multiplier to favour short re-engagement
    resources for users who haven't visited in 3+ days.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'i8k6f7g9h0j1'
down_revision: Union[str, Sequence[str], None] = 'a9743399b22f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('last_active_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('users', 'last_active_at')