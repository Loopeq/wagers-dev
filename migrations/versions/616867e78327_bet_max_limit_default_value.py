"""bet max limit default value

Revision ID: 616867e78327
Revises: ef6e3d889bb8
Create Date: 2025-03-24 21:20:34.190017

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "616867e78327"
down_revision: Union[str, None] = "ef6e3d889bb8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("bet", sa.Column("limit", sa.Integer(), nullable=True))
    op.execute('UPDATE bet SET "limit" = 0 WHERE "limit" IS NULL')
    op.alter_column("bet", "limit", nullable=False)

    op.drop_index("idx_bet_latest_version", table_name="bet")
    op.create_index(
        "idx_bet_latest_version",
        "bet",
        ["match_id", "type", "period", "version"],
        unique=False,
        postgresql_ops={"version": "desc"},
    )


def downgrade() -> None:
    op.drop_index(
        "idx_bet_latest_version", table_name="bet", postgresql_ops={"version": "desc"}
    )
    op.create_index(
        "idx_bet_latest_version",
        "bet",
        ["match_id", "type", "period", sa.text("version DESC")],
        unique=False,
    )
    op.drop_column("bet", "limit")
