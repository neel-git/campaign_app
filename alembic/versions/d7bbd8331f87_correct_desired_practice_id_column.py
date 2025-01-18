"""correct desired_practice_id column

Revision ID: d7bbd8331f87
Revises: c549e1f29e92
Create Date: 2025-01-18 17:03:44.200013

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d7bbd8331f87"
down_revision: Union[str, None] = "c549e1f29e92"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        op.drop_constraint("fk_user_practice", "users", type_="foreignkey")
    except:
        pass

    # Drop the practice_id column
    op.drop_column("users", "practice_id")

    # Add desired_practice_id column
    op.add_column(
        "users", sa.Column("desired_practice_id", sa.BigInteger(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("users", "desired_practice_id")

    # Add back the practice_id column with foreign key
    op.add_column("users", sa.Column("practice_id", sa.BigInteger(), nullable=True))
    op.create_foreign_key(
        "fk_user_practice", "users", "practices", ["practice_id"], ["id"]
    )
