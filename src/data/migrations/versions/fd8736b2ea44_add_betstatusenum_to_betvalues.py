"""add betStatusEnum to betValues

Revision ID: fd8736b2ea44
Revises: b95e9cfea20f
Create Date: 2024-09-14 21:16:16.080241

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fd8736b2ea44'
down_revision: Union[str, None] = 'b95e9cfea20f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

betstatusenum = sa.Enum('open', 'closed', name='betstatusenum')


def upgrade() -> None:
    betstatusenum.create(op.get_bind())

    op.add_column('bet_value', sa.Column('status', betstatusenum, nullable=False))


def downgrade() -> None:
    op.drop_column('bet_value', 'status')
