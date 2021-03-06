"""Add Signal table

Revision ID: 1701130ddc0e
Revises: 1e51050924ca
Create Date: 2014-11-01 21:29:27.970678

"""

# revision identifiers, used by Alembic.
revision = '1701130ddc0e'
down_revision = '1e51050924ca'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('signal',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('stock_point_id', sa.Integer(), nullable=True),
    sa.Column('is_buy_signal', sa.Boolean(), nullable=False),
    sa.Column('signal_type', sa.String(length=64), nullable=False),
    sa.Column('description', sa.String(length=1024), nullable=True),
    sa.ForeignKeyConstraint(['stock_point_id'], ['stock_point.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('signal')
    ### end Alembic commands ###
