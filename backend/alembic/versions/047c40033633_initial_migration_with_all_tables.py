"""Initial migration with all tables

Revision ID: 047c40033633
Revises: 
Create Date: 2025-12-30 00:58:49.485835

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '047c40033633'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create store_master table
    op.create_table('store_master',
        sa.Column('store_id', sa.String(length=50), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('zone', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('store_id')
    )
    
    # Create sku_master table
    op.create_table('sku_master',
        sa.Column('sku_id', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('mrp', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.PrimaryKeyConstraint('sku_id')
    )
    
    # Create raw_uploads table
    op.create_table('raw_uploads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uploaded_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('file_name', sa.String(), nullable=True),
        sa.Column('file_type', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('error_report', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create sales_daily table
    op.create_table('sales_daily',
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('store_id', sa.String(), nullable=False),
        sa.Column('sku_id', sa.String(), nullable=False),
        sa.Column('units_sold', sa.Integer(), nullable=True),
        sa.Column('selling_price', sa.Numeric(), nullable=True),
        sa.ForeignKeyConstraint(['sku_id'], ['sku_master.sku_id'], ),
        sa.ForeignKeyConstraint(['store_id'], ['store_master.store_id'], ),
        sa.PrimaryKeyConstraint('date', 'store_id', 'sku_id')
    )
    
    # Create inventory_batches table
    op.create_table('inventory_batches',
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('store_id', sa.String(), nullable=False),
        sa.Column('sku_id', sa.String(), nullable=False),
        sa.Column('batch_id', sa.String(), nullable=False),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('on_hand_qty', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['sku_id'], ['sku_master.sku_id'], ),
        sa.ForeignKeyConstraint(['store_id'], ['store_master.store_id'], ),
        sa.PrimaryKeyConstraint('snapshot_date', 'store_id', 'sku_id', 'batch_id')
    )
    
    # Create purchases table
    op.create_table('purchases',
        sa.Column('received_date', sa.Date(), nullable=False),
        sa.Column('store_id', sa.String(), nullable=False),
        sa.Column('sku_id', sa.String(), nullable=False),
        sa.Column('batch_id', sa.String(), nullable=False),
        sa.Column('received_qty', sa.Integer(), nullable=True),
        sa.Column('unit_cost', sa.Numeric(), nullable=True),
        sa.ForeignKeyConstraint(['sku_id'], ['sku_master.sku_id'], ),
        sa.ForeignKeyConstraint(['store_id'], ['store_master.store_id'], ),
        sa.PrimaryKeyConstraint('received_date', 'store_id', 'sku_id', 'batch_id')
    )
    
    # Create features_store_sku table
    op.create_table('features_store_sku',
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('store_id', sa.String(), nullable=False),
        sa.Column('sku_id', sa.String(), nullable=False),
        sa.Column('v7', sa.Numeric(), nullable=True),
        sa.Column('v14', sa.Numeric(), nullable=True),
        sa.Column('v30', sa.Numeric(), nullable=True),
        sa.Column('volatility', sa.Numeric(), nullable=True),
        sa.ForeignKeyConstraint(['sku_id'], ['sku_master.sku_id'], ),
        sa.ForeignKeyConstraint(['store_id'], ['store_master.store_id'], ),
        sa.PrimaryKeyConstraint('date', 'store_id', 'sku_id')
    )
    
    # Create batch_risk table
    op.create_table('batch_risk',
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('store_id', sa.String(), nullable=False),
        sa.Column('sku_id', sa.String(), nullable=False),
        sa.Column('batch_id', sa.String(), nullable=False),
        sa.Column('days_to_expiry', sa.Integer(), nullable=True),
        sa.Column('expected_sales_to_expiry', sa.Numeric(), nullable=True),
        sa.Column('at_risk_units', sa.Integer(), nullable=True),
        sa.Column('at_risk_value', sa.Numeric(), nullable=True),
        sa.Column('risk_score', sa.Numeric(), nullable=True),
        sa.ForeignKeyConstraint(['sku_id'], ['sku_master.sku_id'], ),
        sa.ForeignKeyConstraint(['store_id'], ['store_master.store_id'], ),
        sa.PrimaryKeyConstraint('snapshot_date', 'store_id', 'sku_id', 'batch_id')
    )
    
    # Create actions table
    op.create_table('actions',
        sa.Column('action_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('action_type', sa.String(length=20), nullable=True),
        sa.Column('from_store', sa.String(length=50), nullable=True),
        sa.Column('to_store', sa.String(length=50), nullable=True),
        sa.Column('sku_id', sa.String(length=100), nullable=True),
        sa.Column('batch_id', sa.String(length=100), nullable=True),
        sa.Column('qty', sa.Integer(), nullable=True),
        sa.Column('discount_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('expected_savings', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(['from_store'], ['store_master.store_id'], ),
        sa.ForeignKeyConstraint(['sku_id'], ['sku_master.sku_id'], ),
        sa.ForeignKeyConstraint(['to_store'], ['store_master.store_id'], ),
        sa.PrimaryKeyConstraint('action_id')
    )
    
    # Create action_outcomes table
    op.create_table('action_outcomes',
        sa.Column('action_id', sa.Integer(), nullable=False),
        sa.Column('measured_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('recovered_value', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('cleared_units', sa.Integer(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['action_id'], ['actions.action_id'], ),
        sa.PrimaryKeyConstraint('action_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order to handle foreign key constraints
    op.drop_table('action_outcomes')
    op.drop_table('actions')
    op.drop_table('batch_risk')
    op.drop_table('features_store_sku')
    op.drop_table('purchases')
    op.drop_table('inventory_batches')
    op.drop_table('sales_daily')
    op.drop_table('raw_uploads')
    op.drop_table('sku_master')
    op.drop_table('store_master')
