"""rework logic

Revision ID: c28147ce0d94
Revises: 1ec65a66964a
Create Date: 2024-09-18 16:30:11.761974

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c28147ce0d94'
down_revision: Union[str, None] = '1ec65a66964a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('bet_value', sa.Column('version', sa.Integer(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('bet_value', 'version')
    # ### end Alembic commands ###
