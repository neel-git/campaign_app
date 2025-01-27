"""make user role nullabe

Revision ID: 66cc46f7c846
Revises: f12914c0dd14
Create Date: 2025-01-24 01:17:36.555048

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "66cc46f7c846"
down_revision: Union[str, None] = "f12914c0dd14"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("users", "role", existing_type=sa.String(50), nullable=True)


def downgrade() -> None:
    op.alter_column("users", "role", existing_type=sa.String(50), nullable=False)
