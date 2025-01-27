"""adding campaigns schedules table


Revision ID: 46ce440e3d5d
Revises: 3806889d5d31
Create Date: 2025-01-24 02:00:56.061776

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "46ce440e3d5d"
down_revision: Union[str, None] = "3806889d5d31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "campaign_schedules",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("campaign_id", sa.BigInteger(), nullable=False),
        sa.Column("scheduled_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), server_default="PENDING"),
        sa.Column("execution_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
    )

    op.create_index(
        "ix_campaign_schedules_status_date",
        "campaign_schedules",
        ["status", "scheduled_date"],
    )


def downgrade():
    op.drop_index("ix_campaign_schedules_status_date")
    op.drop_table("campaign_schedules")
