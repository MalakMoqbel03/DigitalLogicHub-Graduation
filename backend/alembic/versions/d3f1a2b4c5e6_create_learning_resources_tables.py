"""create learning resources tables

Revision ID: d3f1a2b4c5e6
Revises: 9bebe86c8e1e
Create Date: 2026-03-28 10:00:00.000000

Tables created:
  - learning_resources
  - user_learning_resources
  - user_resource_feedback
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'd3f1a2b4c5e6'
down_revision: Union[str, Sequence[str], None] = '9bebe86c8e1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── learning_resources ──────────────────────────────────────────────────
    op.create_table(
        'learning_resources',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('topic', sa.String(255), nullable=False),
        sa.Column('subtopic', sa.String(255), nullable=True),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('difficulty', sa.String(50), nullable=True),
        sa.Column('vark_style', sa.String(50), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('is_short', sa.Boolean(), nullable=True),
        sa.Column('source', sa.String(255), nullable=True),
        sa.Column('external_url', sa.Text(), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
    )
    op.create_index('ix_learning_resources_id', 'learning_resources', ['id'])
    op.create_index('ix_learning_resources_topic', 'learning_resources', ['topic'])
    op.create_index('ix_learning_resources_difficulty', 'learning_resources', ['difficulty'])

    # ── user_learning_resources ─────────────────────────────────────────────
    op.create_table(
        'user_learning_resources',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('learning_resource_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['learning_resource_id'], ['learning_resources.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_ulr_user_id', 'user_learning_resources', ['user_id'])
    op.create_index('ix_ulr_resource_id', 'user_learning_resources', ['learning_resource_id'])
    # Prevent duplicate tracking rows for the same user+resource
    op.create_unique_constraint(
        'uq_user_learning_resource',
        'user_learning_resources',
        ['user_id', 'learning_resource_id'],
    )

    # ── user_resource_feedback ──────────────────────────────────────────────
    op.create_table(
        'user_resource_feedback',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('learning_resource_id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=True),          # 1-5
        sa.Column('liked', sa.Boolean(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True,
                  server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['learning_resource_id'], ['learning_resources.id'], ondelete='CASCADE'),
        sa.CheckConstraint('rating IS NULL OR (rating >= 1 AND rating <= 5)',
                           name='ck_feedback_rating_range'),
    )
    op.create_index('ix_urf_user_id', 'user_resource_feedback', ['user_id'])


def downgrade() -> None:
    op.drop_table('user_resource_feedback')
    op.drop_table('user_learning_resources')
    op.drop_table('learning_resources')