"""add recommender performance indexes

Revision ID: l1o0k1l3m4n5
Revises: k0n9j0k2l3m4
Create Date: 2024-01-01 00:00:00.000000

Why these indexes exist
───────────────────────
The hybrid recommender runs 6–8 DB queries per request across 4 tables.
Without indexes every query does a full sequential scan.  With 200+ users
and 519 resources the hottest tables (user_resource_feedback,
user_learning_resources) can have 100 k+ rows.  These indexes convert each
seq scan into an O(log n) B-tree lookup.

Idempotency note (2026-06-19)
──────────────────────────────
This migration uses raw `CREATE INDEX IF NOT EXISTS` / `DROP INDEX IF EXISTS`
via op.execute() instead of op.create_index()/op.drop_index().  Alembic's
op.create_index() does NOT support an `if_not_exists` flag in this version —
passing postgresql_if_not_exists raised ArgumentError.  Raw SQL is the
correct and portable way to make this idempotent, since the database was
previously left in a partially-applied state by an earlier failed deploy.

Index-by-index rationale
─────────────────────────
1.  ix_ulr_user_id
    user_learning_resources filtered by user_id in _get_viewed_ids() and
    collaborative _get_user_liked_resource_ids().  Single-column because the
    most common query is "all resources for this user."

2.  ix_ulr_resource_id
    Covers the reverse lookup (all users who viewed a resource) needed by
    the collaborative aggregation query.

3.  ix_urf_user_id  +  4. ix_urf_resource_id
    user_resource_feedback is hit 3 separate times per recommender call
    (liked==False, rating<=2, and the positive-feedback filter in
    _get_viewed_ids).  All three filter on user_id.  The resource_id index
    covers the IN-subquery pattern.

5.  ix_urf_user_resource  (COMPOSITE — the most important one)
    Covers WHERE user_id = ? AND learning_resource_id IN (...) in a single
    index scan.  Composite order: user_id first (equality filter), then
    learning_resource_id (IN filter).  This is the pattern used by
    _get_viewed_ids positive-feedback sub-query and submit_feedback upsert.

6.  ix_lr_difficulty
    learning_resources filtered by difficulty in content_based.
    519 rows now, but the table grows with every new resource added.

7.  ix_lr_vark_style
    Used in the ORDER BY CASE expression for VARK-priority sorting.
    PostgreSQL can use this to avoid a full sort when the planner deems it
    cheaper.

8.  ix_um_user_id
    user_misconceptions filtered by user_id in _get_active_misconception_tags.
    Composite with concept_tag also added since we always fetch both.
"""
from alembic import op


revision = 'l1o0k1l3m4n5'
down_revision = 'k0n9j0k2l3m4'
branch_labels = None
depends_on = None


def upgrade():
    # Raw SQL with IF NOT EXISTS — safe to re-run even if some/all of these
    # indexes already exist from a prior partial deploy.

    # ── user_learning_resources ────────────────────────────────────────────
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ulr_user_id "
        "ON user_learning_resources (user_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ulr_resource_id "
        "ON user_learning_resources (learning_resource_id)"
    )

    # ── user_resource_feedback ─────────────────────────────────────────────
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_urf_user_id "
        "ON user_resource_feedback (user_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_urf_resource_id "
        "ON user_resource_feedback (learning_resource_id)"
    )
    # Composite index — most critical; covers the 2-column WHERE pattern
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_urf_user_resource "
        "ON user_resource_feedback (user_id, learning_resource_id)"
    )

    # ── learning_resources ─────────────────────────────────────────────────
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_lr_difficulty "
        "ON learning_resources (difficulty)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_lr_vark_style "
        "ON learning_resources (vark_style)"
    )

    # ── user_misconceptions ────────────────────────────────────────────────
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_um_user_id "
        "ON user_misconceptions (user_id)"
    )
    # Composite: covers ORDER BY count DESC after the user_id filter
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_um_user_count "
        "ON user_misconceptions (user_id, count)"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_um_user_count")
    op.execute("DROP INDEX IF EXISTS ix_um_user_id")
    op.execute("DROP INDEX IF EXISTS ix_lr_vark_style")
    op.execute("DROP INDEX IF EXISTS ix_lr_difficulty")
    op.execute("DROP INDEX IF EXISTS ix_urf_user_resource")
    op.execute("DROP INDEX IF EXISTS ix_urf_resource_id")
    op.execute("DROP INDEX IF EXISTS ix_urf_user_id")
    op.execute("DROP INDEX IF EXISTS ix_ulr_resource_id")
    op.execute("DROP INDEX IF EXISTS ix_ulr_user_id")