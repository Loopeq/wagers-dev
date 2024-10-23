"""Create database

Revision ID: a7e862fd54ad
Revises: 
Create Date: 2024-10-22 22:01:04.569469

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7e862fd54ad'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('sport',
    sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('league',
    sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('sport_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['sport_id'], ['sport.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('match',
    sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('league_id', sa.Integer(), nullable=False),
    sa.Column('start_time', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['league_id'], ['league.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('bet',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('match_id', sa.Integer(), nullable=False),
    sa.Column('point', sa.Float(), nullable=False),
    sa.Column('home_cf', sa.Float(), nullable=False),
    sa.Column('away_cf', sa.Float(), nullable=False),
    sa.Column('type', sa.Enum('total', 'spread', 'team_total', name='bettypeenum'), nullable=False),
    sa.Column('period', sa.Integer(), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['match_id'], ['match.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('match_member',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('match_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('status', sa.Enum('win', 'lose', name='matchresultenum'), nullable=True),
    sa.Column('side', sa.Enum('home', 'away', name='matchsideenum'), nullable=False),
    sa.ForeignKeyConstraint(['match_id'], ['match.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('match_id', 'side', name='uq_match_combination')
    )
    op.create_table('bet_change',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('old_bet_id', sa.Integer(), nullable=False),
    sa.Column('new_bet_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['new_bet_id'], ['bet.id'], ),
    sa.ForeignKeyConstraint(['old_bet_id'], ['bet.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('bet_change')
    op.drop_table('match_member')
    op.drop_table('bet')
    op.drop_table('match')
    op.drop_table('league')
    op.drop_table('sport')
