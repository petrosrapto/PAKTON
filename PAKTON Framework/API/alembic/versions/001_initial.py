"""Initial migration - create users and conversations tables

Revision ID: 001_initial
Revises: 
Create Date: 2025-11-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)

    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('thread_id', sa.String(length=255), nullable=False),
        sa.Column('user_email', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_email'], ['users.email'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('thread_id')
    )
    op.create_index(op.f('ix_conversations_thread_id'), 'conversations', ['thread_id'], unique=False)
    op.create_index(op.f('ix_conversations_user_email'), 'conversations', ['user_email'], unique=False)


def downgrade() -> None:
    # Drop conversations table first (due to foreign key constraint)
    op.drop_index(op.f('ix_conversations_user_email'), table_name='conversations')
    op.drop_index(op.f('ix_conversations_thread_id'), table_name='conversations')
    op.drop_table('conversations')
    
    # Drop users table
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
