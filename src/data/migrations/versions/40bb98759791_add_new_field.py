"""add new field

Revision ID: 40bb98759791
Revises: b0d441d45ebd
Create Date: 2024-09-23 15:39:02.802295

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '40bb98759791'
down_revision: Union[str, None] = 'b0d441d45ebd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('bet_value_change', sa.Column('is_new', sa.Boolean(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('bet_value_change', 'is_new')
    # ### end Alembic commands ###