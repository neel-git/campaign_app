"""make user role nullable

Revision ID: e6995ffb3981
Revises: e4d980337bed
Create Date: 2025-01-23 10:24:22.938916

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6995ffb3981'
down_revision: Union[str, None] = 'e4d980337bed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('users', 'role',
        existing_type=sa.String(50),
        nullable=True
    )


def downgrade() -> None:
    op.alter_column('users', 'role',
        existing_type=sa.String(50),
        nullable=False
    )
