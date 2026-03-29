"""Add 'moneyline' to BetTypeEnum

Revision ID: 18bea209d5ff
Revises: ed019910fece
Create Date: 2025-04-06 21:13:15.559261

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "18bea209d5ff"
down_revision: Union[str, None] = "ed019910fece"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(f"ALTER TYPE bettypeenum ADD VALUE IF NOT EXISTS 'moneyline'")


def downgrade() -> None:
    pass
