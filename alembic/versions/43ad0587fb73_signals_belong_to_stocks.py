"""Signals belong to Stocks

Revision ID: 43ad0587fb73
Revises: 47e3ff6a778c
Create Date: 2014-11-15 22:17:51.961132

"""

# revision identifiers, used by Alembic.
revision = '43ad0587fb73'
down_revision = '47e3ff6a778c'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('signal', sa.Column('created_date', sa.Date(), nullable=False))
    op.add_column('signal', sa.Column('expiration_date', sa.Date(), nullable=False))
    op.add_column('signal', sa.Column('stock_id', sa.Integer(), nullable=True))
    op.add_column('signal', sa.Column('weight', sa.Float(asdecimal=True), nullable=False))
    op.drop_column('signal', 'stock_point_id')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('signal', sa.Column('stock_point_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_column('signal', 'weight')
    op.drop_column('signal', 'stock_id')
    op.drop_column('signal', 'expiration_date')
    op.drop_column('signal', 'created_date')
    ### end Alembic commands ###
