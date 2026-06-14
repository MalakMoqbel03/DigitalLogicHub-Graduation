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
    # ── user_learning_resources ────────────────────────────────────────────
    op.create_index(
        'ix_ulr_user_id',
        'user_learning_resources',
        ['user_id'],
    )
    op.create_index(
        'ix_ulr_resource_id',
        'user_learning_resources',
        ['learning_resource_id'],
    )

    # ── user_resource_feedback ─────────────────────────────────────────────
    op.create_index(
        'ix_urf_user_id',
        'user_resource_feedback',
        ['user_id'],
    )
    op.create_index(
        'ix_urf_resource_id',
        'user_resource_feedback',
        ['learning_resource_id'],
    )
    # Composite index — most critical; covers the 2-column WHERE pattern
    op.create_index(
        'ix_urf_user_resource',
        'user_resource_feedback',
        ['user_id', 'learning_resource_id'],
    )

    # ── learning_resources ─────────────────────────────────────────────────
    op.create_index(
        'ix_lr_difficulty',
        'learning_resources',
        ['difficulty'],
    )
    op.create_index(
        'ix_lr_vark_style',
        'learning_resources',
        ['vark_style'],
    )

    # ── user_misconceptions ────────────────────────────────────────────────
    op.create_index(
        'ix_um_user_id',
        'user_misconceptions',
        ['user_id'],
    )
    # Composite: covers ORDER BY count DESC after the user_id filter
    op.create_index(
        'ix_um_user_count',
        'user_misconceptions',
        ['user_id', 'count'],
    )


def downgrade():
    op.drop_index('ix_um_user_count',    table_name='user_misconceptions')
    op.drop_index('ix_um_user_id',       table_name='user_misconceptions')
    op.drop_index('ix_lr_vark_style',    table_name='learning_resources')
    op.drop_index('ix_lr_difficulty',    table_name='learning_resources')
    op.drop_index('ix_urf_user_resource',table_name='user_resource_feedback')
    op.drop_index('ix_urf_resource_id',  table_name='user_resource_feedback')
    op.drop_index('ix_urf_user_id',      table_name='user_resource_feedback')
    op.drop_index('ix_ulr_resource_id',  table_name='user_learning_resources')
    op.drop_index('ix_ulr_user_id',      table_name='user_learning_resources')