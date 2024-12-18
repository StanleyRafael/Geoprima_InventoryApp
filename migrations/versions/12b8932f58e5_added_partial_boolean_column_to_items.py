"""Added partial boolean column to items

Revision ID: 12b8932f58e5
Revises: c76755304729
Create Date: 2024-11-28 11:15:27.557773

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '12b8932f58e5'
down_revision = 'c76755304729'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('item_list', schema=None) as batch_op:
        batch_op.add_column(sa.Column('partial', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('item_list', schema=None) as batch_op:
        batch_op.drop_column('partial')

    # ### end Alembic commands ###
