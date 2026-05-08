"""add user profile fields and resource quiz tables

Revision ID: k1n9j0k2l3m4
Revises: j9m8i9j1k2l3
Create Date: 2025-05-05 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'k1n9j0k2l3m4'
down_revision: Union[str, Sequence[str], None] = 'j9m8i9j1k2l3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Add profile columns to users ──────────────────────────────────────
    op.add_column('users', sa.Column('university_name', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('major', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('study_year', sa.String(50), nullable=True))

    # ── 2. Resource quiz questions table ─────────────────────────────────────
    op.create_table(
        'resource_quiz_questions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('learning_resource_id', sa.Integer(),
                  sa.ForeignKey('learning_resources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('option_a', sa.Text(), nullable=False),
        sa.Column('option_b', sa.Text(), nullable=False),
        sa.Column('option_c', sa.Text(), nullable=False),
        sa.Column('option_d', sa.Text(), nullable=False),
        sa.Column('correct_option', sa.String(1), nullable=False),   # 'a','b','c','d'
        sa.Column('concept_tag', sa.String(255), nullable=True),      # for misconception tracking
    )
    op.create_index('ix_rqq_resource', 'resource_quiz_questions',
                    ['learning_resource_id'])

    # ── 3. User resource quiz attempts ───────────────────────────────────────
    op.create_table(
        'user_resource_quiz_attempts',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('learning_resource_id', sa.Integer(),
                  sa.ForeignKey('learning_resources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_id', sa.Integer(),
                  sa.ForeignKey('resource_quiz_questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chosen_option', sa.String(1), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('answered_at', sa.DateTime(), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_urqa_user_resource', 'user_resource_quiz_attempts',
                    ['user_id', 'learning_resource_id'])


def downgrade() -> None:
    op.drop_index('ix_urqa_user_resource', table_name='user_resource_quiz_attempts')
    op.drop_table('user_resource_quiz_attempts')
    op.drop_index('ix_rqq_resource', table_name='resource_quiz_questions')
    op.drop_table('resource_quiz_questions')
    op.drop_column('users', 'study_year')
    op.drop_column('users', 'major')
    op.drop_column('users', 'university_name')