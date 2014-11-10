"""Force OHLC data to be non-null

Revision ID: 47e3ff6a778c
Revises: 1701130ddc0e
Create Date: 2014-11-10 17:48:43.617441

"""

# revision identifiers, used by Alembic.
revision = '47e3ff6a778c'
down_revision = '1701130ddc0e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('stock_point', 'adj_close',
               existing_type=sa.REAL(),
               nullable=False)
    op.alter_column('stock_point', 'close',
               existing_type=sa.REAL(),
               nullable=False)
    op.alter_column('stock_point', 'date',
               existing_type=sa.DATE(),
               nullable=False)
    op.alter_column('stock_point', 'high',
               existing_type=sa.REAL(),
               nullable=False)
    op.alter_column('stock_point', 'low',
               existing_type=sa.REAL(),
               nullable=False)
    op.alter_column('stock_point', 'open',
               existing_type=sa.REAL(),
               nullable=False)
    op.alter_column('stock_point', 'stock_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('stock_point', 'volume',
               existing_type=sa.INTEGER(),
               nullable=False)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('stock_point', 'volume',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('stock_point', 'stock_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('stock_point', 'open',
               existing_type=sa.REAL(),
               nullable=True)
    op.alter_column('stock_point', 'low',
               existing_type=sa.REAL(),
               nullable=True)
    op.alter_column('stock_point', 'high',
               existing_type=sa.REAL(),
               nullable=True)
    op.alter_column('stock_point', 'date',
               existing_type=sa.DATE(),
               nullable=True)
    op.alter_column('stock_point', 'close',
               existing_type=sa.REAL(),
               nullable=True)
    op.alter_column('stock_point', 'adj_close',
               existing_type=sa.REAL(),
               nullable=True)
    ### end Alembic commands ###