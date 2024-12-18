"""Initial migration

Revision ID: 5eff42c271f9
Revises: 
Create Date: 2024-10-17 15:19:19.854918

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5eff42c271f9'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('item_list',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('nama_barang', sa.String(length=100), nullable=False),
    sa.Column('tanggal_masuk', sa.Date(), nullable=False),
    sa.Column('tanggal_keluar', sa.Date(), nullable=True),
    sa.Column('nomor_seri', sa.String(length=50), nullable=False),
    sa.Column('nama_pembeli_pemasok', sa.String(length=100), nullable=False),
    sa.Column('tipe_barang', sa.Enum('barang_jual', 'spare_part', 'barang_sewa', name='tipe_barang_enum'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nomor_seri')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('item_list')
    # ### end Alembic commands ###
