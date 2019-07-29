"""Adds new enumerator for event sub types

Revision ID: 8d6e87fab399
Revises: e6f353653628
Create Date: 2019-06-28 03:03:12.637687

"""
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8d6e87fab399'
down_revision = 'e6f353653628'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    op.execute('ALTER TYPE eventactionsubtypes RENAME TO _eventactionsubtypes')
    eventactionsubtypes = postgresql.ENUM('STATUS', 'TAG', 'SYSTEM', name='eventactionsubtypes')
    eventactionsubtypes.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE events ALTER COLUMN sub_type TYPE eventactionsubtypes USING sub_type::_eventactionsubtypes::text::eventactionsubtypes')
    op.execute('DROP TYPE _eventactionsubtypes')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    op.execute('ALTER TYPE eventactionsubtypes RENAME TO _eventactionsubtypes')
    eventactionsubtypes = postgresql.ENUM('STATUS', 'TAG', name='eventactionsubtypes')
    eventactionsubtypes.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE events ALTER COLUMN sub_type TYPE eventactionsubtypes USING sub_type::_eventactionsubtypes::text::eventactionsubtypes')
    op.execute('DROP TYPE _eventactionsubtypes')

    # ### end Alembic commands ###