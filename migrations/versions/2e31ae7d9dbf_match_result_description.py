"""match result description

Revision ID: 2e31ae7d9dbf
Revises: 18bea209d5ff
Create Date: 2025-04-16 22:13:54.638110

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2e31ae7d9dbf"
down_revision: Union[str, None] = "18bea209d5ff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("match_result", sa.Column("description", sa.String(), nullable=False))


def downgrade() -> None:
    op.drop_index(op.f("ix_match_result_description"), table_name="match_result")
