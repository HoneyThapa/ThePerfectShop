"""Add job execution tracking table

Revision ID: 002_add_job_execution_tracking
Revises: 047c40033633
Create Date: 2025-12-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_job_execution_tracking'
down_revision = '047c40033633'
branch_labels = None
depends_on = None


def upgrade():
    """Add job execution tracking table."""
    op.create_table(
        'job_executions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('job_name', sa.String(length=100), nullable=False),
        sa.Column('job_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('started_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('result_summary', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    """Remove job execution tracking table."""
    op.drop_table('job_executions')