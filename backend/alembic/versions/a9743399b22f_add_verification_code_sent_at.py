"""add_verification_code_sent_at

Revision ID: a9743399b22f
Revises: deca9b784431
Create Date: 2026-04-28 17:14:19.134336

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime



# revision identifiers, used by Alembic.
revision: str = 'a9743399b22f'
down_revision: Union[str, Sequence[str], None] = 'deca9b784431'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('users', sa.Column('verification_code_sent_at', sa.DateTime(), nullable=True))

def downgrade():
    op.drop_column('users', 'verification_code_sent_at')


