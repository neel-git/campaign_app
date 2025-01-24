"""create practice association table

Revision ID: 1871c9ff2099
Revises: ef4b709f1703
Create Date: 2025-01-24 02:06:30.604748

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1871c9ff2099"
down_revision: Union[str, None] = "ef4b709f1703"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "campaign_practice_associations",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("campaign_id", sa.BigInteger(), nullable=False),
        sa.Column("practice_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["practice_id"], ["practices.id"], ondelete="CASCADE"),
    )

    # Indexes for faster lookups
    op.create_index(
        "ix_campaign_practice_campaign_id",
        "campaign_practice_associations",
        ["campaign_id"],
    )
    op.create_index(
        "ix_campaign_practice_practice_id",
        "campaign_practice_associations",
        ["practice_id"],
    )
    # Unique constraint to prevent duplicate associations
    op.create_unique_constraint(
        "uq_campaign_practice",
        "campaign_practice_associations",
        ["campaign_id", "practice_id"],
    )


def downgrade():
    op.drop_index("ix_campaign_practice_practice_id")
    op.drop_index("ix_campaign_practice_campaign_id")
    op.drop_constraint("uq_campaign_practice", "campaign_practice_associations")
    op.drop_table("campaign_practice_associations")
