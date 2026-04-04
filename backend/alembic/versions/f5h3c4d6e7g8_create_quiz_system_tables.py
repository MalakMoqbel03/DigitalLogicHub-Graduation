"""create quiz system tables and update users

Revision ID: f5h3c4d6e7g8
Revises: e4g2b3c5d6f7
Create Date: 2026-03-28 10:02:00.000000

Tables created:
  - quizzes
  - quiz_questions
  - quiz_answers
  - user_quiz_attempts
  - user_question_responses

Columns added to users:
  - learning_style
  - level
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'f5h3c4d6e7g8'
down_revision: Union[str, Sequence[str], None] = 'e4g2b3c5d6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Add learning_style + level to users (safe: only adds if missing) ────
    # Use a try/except pattern via execute so it's idempotent
    conn = op.get_bind()
    cols = {row[0] for row in conn.execute(
        sa.text("SELECT column_name FROM information_schema.columns WHERE table_name='users'")
    )}
    if 'learning_style' not in cols:
        op.add_column('users', sa.Column('learning_style', sa.String(), nullable=True))
    if 'level' not in cols:
        op.add_column('users', sa.Column('level', sa.String(), nullable=True))

    # ── quizzes ─────────────────────────────────────────────────────────────
    # One quiz per topic × difficulty × quiz_type combination.
    op.create_table(
        'quizzes',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('topic', sa.String(255), nullable=False),
        sa.Column('subtopic', sa.String(255), nullable=True),
        sa.Column('difficulty', sa.String(50), nullable=False),
        # difficulty: beginner | intermediate | advanced
        sa.Column('quiz_type', sa.String(50), nullable=False,
                  server_default=sa.text("'practice'")),
        # quiz_type: practice | assessment
        sa.Column('vark_style', sa.String(50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.CheckConstraint(
            "difficulty IN ('beginner','intermediate','advanced')",
            name='ck_quiz_difficulty',
        ),
        sa.CheckConstraint(
            "quiz_type IN ('practice','assessment')",
            name='ck_quiz_type',
        ),
    )
    op.create_index('ix_quizzes_topic', 'quizzes', ['topic'])
    op.create_index('ix_quizzes_difficulty', 'quizzes', ['difficulty'])

    # ── quiz_questions ───────────────────────────────────────────────────────
    op.create_table(
        'quiz_questions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('quiz_id', sa.Integer(), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('cognitive_level', sa.String(50), nullable=True),
        # cognitive_level: remember | apply | analyze
        sa.Column('concept_tag', sa.String(255), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            "cognitive_level IS NULL OR cognitive_level IN ('remember','apply','analyze')",
            name='ck_qq_cognitive_level',
        ),
    )
    op.create_index('ix_quiz_questions_quiz_id', 'quiz_questions', ['quiz_id'])

    # ── quiz_answers ─────────────────────────────────────────────────────────
    # Stores the MCQ options for each quiz question, including misconception data.
    op.create_table(
        'quiz_answers',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('answer_text', sa.Text(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        # Misconception fields: populated for wrong-answer options
        sa.Column('misconception_tag', sa.String(255), nullable=True),
        sa.Column('misconception_type', sa.String(255), nullable=True),
        sa.Column('severity', sa.String(50), nullable=True),
        # severity: low | medium | high
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['question_id'], ['quiz_questions.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_quiz_answers_question_id', 'quiz_answers', ['question_id'])

    # ── user_quiz_attempts ───────────────────────────────────────────────────
    op.create_table(
        'user_quiz_attempts',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quiz_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('total_questions', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True,
                  server_default=sa.text('NOW()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_uqa_user_id', 'user_quiz_attempts', ['user_id'])
    op.create_index('ix_uqa_quiz_id', 'user_quiz_attempts', ['quiz_id'])

    # ── user_question_responses ──────────────────────────────────────────────
    # Stores each individual answer choice within a quiz attempt,
    # along with misconception tracking for wrong answers.
    op.create_table(
        'user_question_responses',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('attempt_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('selected_answer_id', sa.Integer(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('misconception_tag', sa.String(255), nullable=True),
        # Copied from the chosen answer's misconception_tag for fast querying
        sa.Column('answered_at', sa.DateTime(), nullable=True,
                  server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['attempt_id'], ['user_quiz_attempts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['quiz_questions.id']),
        sa.ForeignKeyConstraint(['selected_answer_id'], ['quiz_answers.id']),
    )
    op.create_index('ix_uqr_attempt_id', 'user_question_responses', ['attempt_id'])
    op.create_index('ix_uqr_misconception', 'user_question_responses', ['misconception_tag'])


def downgrade() -> None:
    op.drop_table('user_question_responses')
    op.drop_table('user_quiz_attempts')
    op.drop_table('quiz_answers')
    op.drop_table('quiz_questions')
    op.drop_table('quizzes')
    # Only drop columns if you're sure they weren't there before this migration
    op.drop_column('users', 'level')
    op.drop_column('users', 'learning_style')