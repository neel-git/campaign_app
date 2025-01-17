"""create practice table

Revision ID: 1b937729fa55
Revises: 
Create Date: 2025-01-17 01:13:55.232992

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1b937729fa55"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create practices table
    op.create_table(
        "practices",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("name"),
    )

    # Create practice_user_assignments table
    op.create_table(
        "practice_user_assignments",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "practice_id",
            sa.BigInteger(),
            sa.ForeignKey("practices.id"),
            nullable=False,
        ),
        sa.Column(
            "user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column(
            "assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )


def downgrade() -> None:
    op.drop_table("practice_user_assignments")
    op.drop_table("practices")
