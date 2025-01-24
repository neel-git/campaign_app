"""create campaign history table

Revision ID: ef4b709f1703
Revises: 46ce440e3d5d
Create Date: 2025-01-24 02:05:32.765172

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ef4b709f1703"
down_revision: Union[str, None] = "46ce440e3d5d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "campaign_history",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("campaign_id", sa.BigInteger(), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("performed_by", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["performed_by"], ["users.id"], ondelete="CASCADE"),
    )

    # Index for faster history lookups by campaign
    op.create_index(
        "ix_campaign_history_campaign_id", "campaign_history", ["campaign_id"]
    )


def downgrade():
    op.drop_index("ix_campaign_history_campaign_id")
    op.drop_table("campaign_history")
