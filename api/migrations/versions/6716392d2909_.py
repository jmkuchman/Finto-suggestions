""" Add sub_type (and enum type) and value for handle action events more easier, refactored also suggestionstatustypes

Revision ID: 6716392d2909
Revises: 224ae0a46cea
Create Date: 2019-01-22 10:12:26.709483

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '6716392d2909'
down_revision = '224ae0a46cea'
branch_labels = None
depends_on = None

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('events', sa.Column('value', sa.Text(), nullable=True))

    event_action_sub_types = postgresql.ENUM('STATUS', 'TAG', name='eventactionsubtypes')
    event_action_sub_types.create(op.get_bind(), checkfirst=False)
    op.add_column('events', sa.Column('sub_type', sa.Enum('STATUS', 'TAG', name='eventactionsubtypes'), nullable=True))

    op.execute('ALTER TYPE suggestionstatustypes RENAME TO _suggestionstatustypes')
    suggestions_status_types = postgresql.ENUM('RECEIVED', 'READ ', 'REJECTED', 'ACCEPTED', 'RETAINED', 'ARCHIVED', name='suggestionstatustypes')
    suggestions_status_types.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE suggestions ALTER COLUMN status TYPE suggestionstatustypes USING status::_suggestionstatustypes::text::suggestionstatustypes')
    op.execute('DROP TYPE _suggestionstatustypes')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('events', 'value')
    op.drop_column('events', 'sub_type')

    op.execute('DROP TYPE eventactionsubtypes')

    op.execute('ALTER TYPE suggestionstatustypes RENAME TO _suggestionstatustypes')
    suggestions_status_types = postgresql.ENUM('DEFAULT', 'REJECTED', 'ACCEPTED', name='suggestionstatustypes')
    suggestions_status_types.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE suggestions ALTER COLUMN status TYPE suggestionstatustypes USING status::_suggestionstatustypes::text::suggestionstatustypes')
    op.execute('DROP TYPE _suggestionstatustypes')
    # ### end Alembic commands ###
