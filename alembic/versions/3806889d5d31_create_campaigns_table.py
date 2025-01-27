"""create campaigns table

Revision ID: 3806889d5d31
Revises: 66cc46f7c846
Create Date: 2025-01-24 01:18:53.525670

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "3806889d5d31"
down_revision: Union[str, None] = "66cc46f7c846"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create campaigns table first since it's referenced by other tables
    op.create_table(
        "campaigns",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("campaign_type", sa.String(20), nullable=False),
        sa.Column("delivery_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), server_default="DRAFT"),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column("target_roles", postgresql.JSON(), nullable=False),
        sa.Column("copied_from", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["copied_from"], ["campaigns.id"], ondelete="SET NULL"),
    )


def downgrade() -> None:
    op.drop_table("campaigns")
