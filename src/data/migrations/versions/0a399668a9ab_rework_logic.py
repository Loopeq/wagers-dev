"""rework logic

Revision ID: 0a399668a9ab
Revises: fd8736b2ea44
Create Date: 2024-09-16 14:34:31.512939

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0a399668a9ab'
down_revision: Union[str, None] = 'fd8736b2ea44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('bet', sa.Column('match_id', sa.Integer(), nullable=False))
    op.drop_constraint('uq_match_member_combination', 'bet', type_='unique')
    op.create_unique_constraint('uq_match_member_combination', 'bet', ['match_id', 'type', 'period'])
    op.drop_constraint('bet_match_member_id_fkey', 'bet', type_='foreignkey')
    op.create_foreign_key(None, 'bet', 'match', ['match_id'], ['id'])
    op.drop_column('bet', 'match_member_id')
    op.add_column('bet_value', sa.Column('type', sa.Integer()))
    op.alter_column('bet_value', 'type',
                    existing_type=postgresql.ENUM('home', 'away', 'over', 'under', name='betvaluetypeenum'),
                    nullable=False)


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('bet_value', 'type')
    op.add_column('bet', sa.Column('match_member_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'bet', type_='foreignkey')
    op.create_foreign_key('bet_match_member_id_fkey', 'bet', 'match_member', ['match_member_id'], ['id'])
    op.drop_constraint('uq_match_member_combination', 'bet', type_='unique')
    op.create_unique_constraint('uq_match_member_combination', 'bet', ['match_member_id', 'type', 'period'])
    op.drop_column('bet', 'match_id')
    # ### end Alembic commands ###