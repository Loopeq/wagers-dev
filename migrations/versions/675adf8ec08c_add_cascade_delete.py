"""Add cascade delete

Revision ID: 675adf8ec08c
Revises: ba03bc334cef
Create Date: 2024-10-30 23:09:16.436921

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '675adf8ec08c'
down_revision: Union[str, None] = 'ba03bc334cef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('bet_match_id_fkey', 'bet', type_='foreignkey')
    op.create_foreign_key(None, 'bet', 'match', ['match_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('bet_change_new_bet_id_fkey', 'bet_change', type_='foreignkey')
    op.drop_constraint('bet_change_old_bet_id_fkey', 'bet_change', type_='foreignkey')
    op.create_foreign_key(None, 'bet_change', 'bet', ['old_bet_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'bet_change', 'bet', ['new_bet_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('match_member_match_id_fkey', 'match_member', type_='foreignkey')
    op.create_foreign_key(None, 'match_member', 'match', ['match_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'match_member', type_='foreignkey')
    op.create_foreign_key('match_member_match_id_fkey', 'match_member', 'match', ['match_id'], ['id'])
    op.drop_constraint(None, 'bet_change', type_='foreignkey')
    op.drop_constraint(None, 'bet_change', type_='foreignkey')
    op.create_foreign_key('bet_change_old_bet_id_fkey', 'bet_change', 'bet', ['old_bet_id'], ['id'])
    op.create_foreign_key('bet_change_new_bet_id_fkey', 'bet_change', 'bet', ['new_bet_id'], ['id'])
    op.drop_constraint(None, 'bet', type_='foreignkey')
    op.create_foreign_key('bet_match_id_fkey', 'bet', 'match', ['match_id'], ['id'])
    # ### end Alembic commands ###