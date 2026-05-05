"""add topic_cluster to learning_resources

Revision ID: h7j5e6f8g9i0
Revises: g6i4d5e7f8h9
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'h7j5e6f8g9i0'
down_revision = 'g6i4d5e7f8h9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add topic_cluster column to learning_resources
    op.add_column(
        'learning_resources',
        sa.Column('topic_cluster', sa.String(255), nullable=True)
    )

    # Backfill topic_cluster based on topic values
    # These match the TOPIC_CLUSTERS dict in recommender.py
    op.execute("""
        UPDATE learning_resources SET topic_cluster = 'Digital Fundamentals'
        WHERE topic IN ('Digital Basics', 'Digital_Basics');
    """)
    op.execute("""
        UPDATE learning_resources SET topic_cluster = 'Boolean Algebra & Logic'
        WHERE topic IN ('Boolean Algebra', 'Boolean_Algebra', 'Logic Simplification');
    """)
    op.execute("""
        UPDATE learning_resources SET topic_cluster = 'Combinational Logic'
        WHERE topic IN ('Combinational Logic', 'Combinational_Logic');
    """)
    op.execute("""
        UPDATE learning_resources SET topic_cluster = 'Sequential Logic'
        WHERE topic IN ('Sequential Logic', 'Registers & Counters', 'Registers and Counters');
    """)
    op.execute("""
        UPDATE learning_resources SET topic_cluster = 'Finite State Machines'
        WHERE topic IN ('FSM');
    """)
    op.execute("""
        UPDATE learning_resources SET topic_cluster = 'Hardware Description Language'
        WHERE topic IN ('HDL Verilog', 'HDL_Verilog');
    """)
    op.execute("""
        UPDATE learning_resources SET topic_cluster = 'Memory & Performance'
        WHERE topic IN ('Memory Systems', 'Timing and Performance');
    """)
    op.execute("""
        UPDATE learning_resources SET topic_cluster = 'Other'
        WHERE topic_cluster IS NULL;
    """)

    # Create index for fast cluster filtering
    op.create_index(
        'ix_learning_resources_topic_cluster',
        'learning_resources',
        ['topic_cluster']
    )


def downgrade() -> None:
    op.drop_index('ix_learning_resources_topic_cluster', table_name='learning_resources')
    op.drop_column('learning_resources', 'topic_cluster')