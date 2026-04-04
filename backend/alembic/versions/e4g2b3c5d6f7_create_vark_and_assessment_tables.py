"""create vark and assessment tables

Revision ID: e4g2b3c5d6f7
Revises: d3f1a2b4c5e6
Create Date: 2026-03-28 10:01:00.000000

Tables created:
  - vark_questions
  - vark_options
  - user_vark_responses
  - questions
  - answers
  - assessment_sessions
  - user_responses
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'e4g2b3c5d6f7'
down_revision: Union[str, Sequence[str], None] = 'd3f1a2b4c5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── vark_questions ──────────────────────────────────────────────────────
    op.create_table(
        'vark_questions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('question_text', sa.String(), nullable=False),
    )
    op.create_index('ix_vark_questions_id', 'vark_questions', ['id'])

    # ── vark_options ────────────────────────────────────────────────────────
    op.create_table(
        'vark_options',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('option_text', sa.String(), nullable=False),
        sa.Column('vark_type', sa.String(), nullable=False),
        # vark_type values: visual | auditory | reading | kinesthetic
        sa.ForeignKeyConstraint(['question_id'], ['vark_questions.id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            "vark_type IN ('visual','auditory','reading','kinesthetic')",
            name='ck_vark_option_type',
        ),
    )
    op.create_index('ix_vark_options_id', 'vark_options', ['id'])
    op.create_index('ix_vark_options_question_id', 'vark_options', ['question_id'])

    # ── user_vark_responses ─────────────────────────────────────────────────
    op.create_table(
        'user_vark_responses',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('vark_option_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vark_option_id'], ['vark_options.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_uvr_user_id', 'user_vark_responses', ['user_id'])

    # ── questions ───────────────────────────────────────────────────────────
    # Used by the digital systems skill-level assessment
    op.create_table(
        'questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('concept_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('question_text', sa.String(), nullable=False),
        sa.Column('difficulty', sa.String(), nullable=False),
        # difficulty: beginner | intermediate | advanced
        sa.Column('is_entry', sa.Boolean(), nullable=True, server_default=sa.text('false')),
        sa.CheckConstraint(
            "difficulty IN ('beginner','intermediate','advanced')",
            name='ck_question_difficulty',
        ),
    )
    op.create_index('ix_questions_difficulty', 'questions', ['difficulty'])

    # ── answers ─────────────────────────────────────────────────────────────
    op.create_table(
        'answers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('answer_text', sa.String(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=True, server_default=sa.text('false')),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_answers_question_id', 'answers', ['question_id'])

    # ── assessment_sessions ─────────────────────────────────────────────────
    op.create_table(
        'assessment_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True,
                  server_default=sa.text('NOW()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('score', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('level', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_assessment_sessions_user_id', 'assessment_sessions', ['user_id'])

    # ── user_responses ──────────────────────────────────────────────────────
    op.create_table(
        'user_responses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('answer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=True, server_default=sa.text('false')),
        sa.Column('answered_at', sa.DateTime(), nullable=True,
                  server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['session_id'], ['assessment_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id']),
        sa.ForeignKeyConstraint(['answer_id'], ['answers.id']),
    )
    op.create_index('ix_user_responses_session_id', 'user_responses', ['session_id'])


def downgrade() -> None:
    op.drop_table('user_responses')
    op.drop_table('assessment_sessions')
    op.drop_table('answers')
    op.drop_table('questions')
    op.drop_table('user_vark_responses')
    op.drop_table('vark_options')
    op.drop_table('vark_questions')