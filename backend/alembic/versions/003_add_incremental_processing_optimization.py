"""Add incremental processing optimization

Revision ID: 003
Revises: 002
Create Date: 2024-12-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Create data_change_tracking table for incremental processing optimization
    op.create_table('data_change_tracking',
        sa.Column('table_name', sa.String(length=100), nullable=False),
        sa.Column('processing_type', sa.String(length=50), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('last_processed_at', sa.TIMESTAMP(), nullable=False),
        sa.Column('records_processed', sa.Integer(), nullable=False, default=0),
        sa.Column('data_hash', sa.String(length=64), nullable=True),
        sa.Column('change_summary', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('table_name', 'processing_type', 'snapshot_date')
    )
    
    # Create indexes for efficient querying
    op.create_index('idx_data_change_tracking_processing_type', 'data_change_tracking', ['processing_type'])
    op.create_index('idx_data_change_tracking_snapshot_date', 'data_change_tracking', ['snapshot_date'])
    op.create_index('idx_data_change_tracking_last_processed', 'data_change_tracking', ['last_processed_at'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_data_change_tracking_last_processed', table_name='data_change_tracking')
    op.drop_index('idx_data_change_tracking_snapshot_date', table_name='data_change_tracking')
    op.drop_index('idx_data_change_tracking_processing_type', table_name='data_change_tracking')
    
    # Drop table
    op.drop_table('data_change_tracking')