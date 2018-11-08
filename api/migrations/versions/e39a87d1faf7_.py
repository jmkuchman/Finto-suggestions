"""Add tag_label field to events table

Revision ID: e39a87d1faf7
Revises: e008d81a779e
Create Date: 2018-10-29 13:04:29.087149

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e39a87d1faf7'
down_revision = 'e008d81a779e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('events', sa.Column('tag_label', sa.String(length=50), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('events', 'tag_label')
    # ### end Alembic commands ###