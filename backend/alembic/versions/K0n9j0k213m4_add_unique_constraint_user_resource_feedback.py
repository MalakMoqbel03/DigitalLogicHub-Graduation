"""add unique constraint to user_resource_feedback

Revision ID: k0n9j0k2l3m4
Revises: j9m8i9j1k2l3
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op

revision = 'k0n9j0k2l3m4'
down_revision = 'j9m8i9j1k2l3'
branch_labels = None
depends_on = None


def upgrade():
    # Remove any duplicate rows first (keep the latest one per pair)
    op.execute("""
        DELETE FROM user_resource_feedback a
        USING user_resource_feedback b
        WHERE a.id < b.id
          AND a.user_id = b.user_id
          AND a.learning_resource_id = b.learning_resource_id
    """)
    op.create_unique_constraint(
        'uq_user_resource_feedback_user_resource',
        'user_resource_feedback',
        ['user_id', 'learning_resource_id']
    )


def downgrade():
    op.drop_constraint(
        'uq_user_resource_feedback_user_resource',
        'user_resource_feedback',
        type_='unique'
    )