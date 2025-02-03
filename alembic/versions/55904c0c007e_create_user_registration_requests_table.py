"""create user registration requests table

Revision ID: 55904c0c007e
Revises: 829b95b03037
Create Date: 2025-01-24 01:14:39.330677

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "55904c0c007e"
down_revision: Union[str, None] = "829b95b03037"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_registration_requests",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("desired_practice_id", sa.BigInteger(), nullable=False),
        sa.Column("requested_role", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), server_default="PENDING", nullable=False),
        sa.Column("reviewed_by", sa.BigInteger(), nullable=True),
        sa.Column("rejection_reason", sa.String(500), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_registration_request_user",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["desired_practice_id"],
            ["practices.id"],
            name="fk_registration_request_practice",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"],
            ["users.id"],
            name="fk_registration_request_reviewer",
            ondelete="SET NULL",
        ),
    )

    op.create_index(
        "ix_user_registration_requests_user_id",
        "user_registration_requests",
        ["user_id"],
    )
    op.create_index(
        "ix_user_registration_requests_status", "user_registration_requests", ["status"]
    )
    op.create_index(
        "ix_user_registration_requests_desired_practice_id",
        "user_registration_requests",
        ["desired_practice_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_user_registration_requests_desired_practice_id")
    op.drop_index("ix_user_registration_requests_status")
    op.drop_index("ix_user_registration_requests_user_id")

    op.drop_table("user_registration_requests")
