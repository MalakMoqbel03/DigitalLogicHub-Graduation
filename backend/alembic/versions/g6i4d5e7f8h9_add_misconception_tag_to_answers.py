"""add misconception_tag to answers and create user_misconceptions

Revision ID: g6i4d5e7f8h9
Revises: f5h3c4d6e7g8
Create Date: 2026-03-28 11:00:00.000000

Changes:
  - CREATE TABLE user_misconceptions
  - ALTER TABLE answers ADD COLUMN misconception_tag
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

revision: str = 'g6i4d5e7f8h9'
down_revision: Union[str, Sequence[str], None] = 'f5h3c4d6e7g8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # ── user_misconceptions ──────────────────────────────────────────────────
    existing_tables = {
        row[0] for row in conn.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname='public'")
        )
    }

    if 'user_misconceptions' not in existing_tables:
        op.create_table(
            'user_misconceptions',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('concept_tag', sa.String(255), nullable=False),
            sa.Column('count', sa.Integer(), nullable=False, server_default=sa.text('1')),
            sa.Column('first_seen', sa.DateTime(), nullable=True),
            sa.Column('last_seen', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        )
        op.create_index('ix_um_user_id', 'user_misconceptions', ['user_id'])
        op.create_index('ix_um_concept_tag', 'user_misconceptions', ['concept_tag'])

    # ── answers.misconception_tag ────────────────────────────────────────────
    answer_cols = {
        row[0] for row in conn.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name='answers'")
        )
    }
    if 'misconception_tag' not in answer_cols:
        op.add_column('answers', sa.Column('misconception_tag', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('answers', 'misconception_tag')
    op.drop_table('user_misconceptions')