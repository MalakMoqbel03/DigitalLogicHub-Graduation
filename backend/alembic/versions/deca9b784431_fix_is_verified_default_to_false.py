"""fix_is_verified_default_to_false

Revision ID: deca9b784431
Revises: h7j5e6f8g9i0
Create Date: 2026-04-28 16:36:06.407530

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'deca9b784431'
down_revision: Union[str, Sequence[str], None] = 'h7j5e6f8g9i0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.alter_column(
        'users',
        'is_verified',
        existing_type=sa.Boolean(),
        server_default=sa.text('false'),
        existing_nullable=True
    )

def downgrade():
    op.alter_column(
        'users',
        'is_verified',
        existing_type=sa.Boolean(),
        server_default=sa.text('true'),
        existing_nullable=True
    )

