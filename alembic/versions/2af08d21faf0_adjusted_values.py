"""adjusted_values

Revision ID: 2af08d21faf0
Revises: 46841d7388e4
Create Date: 2014-12-02 18:32:10.307516

"""

# revision identifiers, used by Alembic.
revision = '2af08d21faf0'
down_revision = '46841d7388e4'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('stock_point', sa.Column('adj_high', sa.Float(precision=2, asdecimal=True), nullable=True))
    op.add_column('stock_point', sa.Column('adj_low', sa.Float(precision=2, asdecimal=True), nullable=True))
    op.add_column('stock_point', sa.Column('adj_open', sa.Float(precision=2, asdecimal=True), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('stock_point', 'adj_open')
    op.drop_column('stock_point', 'adj_low')
    op.drop_column('stock_point', 'adj_high')
    ### end Alembic commands ###