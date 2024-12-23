"""Add match result model

Revision ID: ba03bc334cef
Revises: 2ab971cd3294
Create Date: 2024-10-30 17:41:16.140379

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba03bc334cef'
down_revision: Union[str, None] = '2ab971cd3294'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('match_result',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('match_id', sa.Integer(), nullable=False),
    sa.Column('period', sa.Integer(), nullable=False),
    sa.Column('team_1_score', sa.Integer(), nullable=False),
    sa.Column('team_2_score', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['match_id'], ['match.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_match_result_match_id'), 'match_result', ['match_id'], unique=False)
    op.create_index(op.f('ix_match_result_period'), 'match_result', ['period'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_match_result_period'), table_name='match_result')
    op.drop_index(op.f('ix_match_result_match_id'), table_name='match_result')
    op.drop_table('match_result')
    # ### end Alembic commands ###
