"""update campaign user relationship

Revision ID: 9dcea3fc5fb6
Revises: d5b29d1bed5a
Create Date: 2025-01-27 02:45:52.646761

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9dcea3fc5fb6"
down_revision: Union[str, None] = "d5b29d1bed5a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_campaigns_created_by", "campaigns", ["created_by"])

    # Add foreign key constraint if not exists
    op.create_foreign_key(
        "fk_campaigns_created_by_users",
        "campaigns",
        "users",
        ["created_by"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_campaigns_created_by_users", "campaigns", type_="foreignkey")

    # Remove the index
    op.drop_index("ix_campaigns_created_by", table_name="campaigns")
