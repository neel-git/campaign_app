"""add full_name and practice_id to user model

Revision ID: c549e1f29e92
Revises: 1b937729fa55
Create Date: 2025-01-18 16:20:07.153954

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c549e1f29e92"
down_revision: Union[str, None] = "1b937729fa55"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("full_name", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("practice_id", sa.BigInteger(), nullable=True))
    op.create_foreign_key(
        "fk_user_practice", "users", "practices", ["practice_id"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_user_practice", "users", type_="foreignkey")
    op.drop_column("users", "practice_id")
    op.drop_column("users", "full_name")
