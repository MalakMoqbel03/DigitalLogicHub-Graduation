"""merge divergent migration branches

Revision ID: n4q2m3n5o6p7
Revises: l1o0k1l3m4n5, M3p1l2m4n5o6
Create Date: 2026-06-19 00:00:00.000000

Why this migration exists
──────────────────────────
Two migrations were independently created with the same down_revision
('j9m8i9j1k2l3'), creating two parallel branches:

  j9m8i9j1k2l3 (add_topic_cluster)
       ├──→ k0n9j0k2l3m4 (unique constraint) → l1o0k1l3m4n5 (recommender indexes)
       └──→ k1n9j0k2l3m4 (user profile + quiz) → M3p1l2m4n5o6 (bookmarks + skipped)

This left Alembic with two "heads" and no way to know which to apply with
`alembic upgrade head`. This merge migration has no schema changes of its
own — it just joins both branch tips into a single head so future
migrations have one clear lineage to build on.

Safe to run regardless of which branch was applied first; SQLAlchemy/Alembic
tracks applied revisions per-database, so users who already have one branch
applied will only have the missing branch's migrations run when this merge
is reached.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'n4q2m3n5o6p7'
down_revision = ('l1o0k1l3m4n5', 'M3p1l2m4n5o6')
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No schema changes — this is purely a merge point.
    pass


def downgrade() -> None:
    # No schema changes to revert.
    pass