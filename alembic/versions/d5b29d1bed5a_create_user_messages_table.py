"""create user messages table

Revision ID: d5b29d1bed5a
Revises: 1871c9ff2099
Create Date: 2025-01-24 10:19:56.057093

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d5b29d1bed5a"
down_revision: Union[str, None] = "1871c9ff2099"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "user_messages",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("campaign_id", sa.BigInteger(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), default=False),
        sa.Column("is_deleted", sa.Boolean(), default=False),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
    )

    op.create_index("ix_user_messages_user_id", "user_messages", ["user_id"])


def downgrade():
    # Drop the index on user_id column
    op.drop_index("ix_user_messages_user_id", table_name="user_messages")

    # Drop the user_messages table
    op.drop_table("user_messages")
