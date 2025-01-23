"""request role change table

Revision ID: e4d980337bed
Revises: dd0c82767c11
Create Date: 2025-01-23 01:57:29.760158

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4d980337bed'
down_revision: Union[str, None] = 'dd0c82767c11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'role_change_requests',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('practice_id', sa.BigInteger(), nullable=False),
        sa.Column('current_role', sa.String(50), nullable=False),
        sa.Column('requested_role', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='PENDING'),
        sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('reviewed_by', sa.BigInteger(), nullable=True),
        sa.Column('rejection_reason', sa.String(500), nullable=True),
        
        # Foreign Key Constraints
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'],
            name='fk_role_change_user_id',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['practice_id'], ['practices.id'],
            name='fk_role_change_practice_id',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['reviewed_by'], ['users.id'],
            name='fk_role_change_reviewer_id',
            ondelete='SET NULL'
        ),
        
        # Indexes
        sa.Index('idx_role_change_user_id', 'user_id'),
        sa.Index('idx_role_change_practice_id', 'practice_id'),
        sa.Index('idx_role_change_status', 'status'),
        sa.Index('idx_role_change_requested_at', 'requested_at'),
    )

    # Add a check constraint for valid status values
    op.execute("""
        ALTER TABLE role_change_requests 
        ADD CONSTRAINT chk_valid_status 
        CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED'))
    """)

def downgrade() -> None:
    # Drop all related indexes first (though they would be dropped with the table)
    op.drop_index('idx_role_change_requested_at')
    op.drop_index('idx_role_change_status')
    op.drop_index('idx_role_change_practice_id')
    op.drop_index('idx_role_change_user_id')
    
    # Drop the table
    op.drop_table('role_change_requests')
