"""create practice user assignment table

Revision ID: 829b95b03037
Revises: 7554c9d0a5a5
Create Date: 2025-01-24 01:13:27.736504

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '829b95b03037'
down_revision: Union[str, None] = '7554c9d0a5a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "practice_user_assignments",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("practice_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["practice_id"],
            ["practices.id"],
            name="fk_practice_user_assignment_practice",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_practice_user_assignment_user",
            ondelete="CASCADE",
        ),
    )

    op.create_index(
        "ix_practice_user_assignments_practice_id",
        "practice_user_assignments",
        ["practice_id"],
    )
    op.create_index(
        "ix_practice_user_assignments_user_id", "practice_user_assignments", ["user_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_practice_user_assignments_user_id")
    op.drop_index("ix_practice_user_assignments_practice_id")

    # Then drop the table
    op.drop_table("practice_user_assignments")

