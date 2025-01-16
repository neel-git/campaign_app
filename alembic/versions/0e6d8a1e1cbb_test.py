"""test

Revision ID: 0e6d8a1e1cbb
Revises: ddc397e00178
Create Date: 2025-01-16 15:21:14.111163

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0e6d8a1e1cbb'
down_revision: Union[str, None] = 'ddc397e00178'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'practices',
        sa.Column('id',sa.BigInteger(),primary_key=True),
        sa.Column('name',sa.String(255),nullable=False),
        sa.Column('description',sa.Text(),nullable=True),
        sa.Column('is_active',sa.Boolean(),nullable)
    )


def downgrade() -> None:
    pass
