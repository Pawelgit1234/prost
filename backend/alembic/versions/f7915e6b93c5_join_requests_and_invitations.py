"""join requests and invitations

Revision ID: f7915e6b93c5
Revises: c6eaa08d3dfc
Create Date: 2025-07-06 18:48:55.700762
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7915e6b93c5'
down_revision: Union[str, None] = 'c6eaa08d3dfc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # --- Create new tables ---
    op.create_table(
        'invitations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.UUID(), nullable=False),
        sa.Column('chat_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('max_uses', sa.Integer(), nullable=True),
        sa.Column('lifetime', sa.Enum('TEN_MINUTES', 'ONE_HOUR', 'ONE_DAY', 'UNLIMITED', name='invitationlifetime'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('chat_id IS NOT NULL OR user_id IS NOT NULL', name='check_invitation_has_target'),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )

    op.create_table(
        'join_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.UUID(), nullable=False),
        sa.Column('sender_user_id', sa.Integer(), nullable=False),
        sa.Column('chat_id', sa.Integer(), nullable=True),
        sa.Column('receiver_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('chat_id IS NOT NULL OR receiver_user_id IS NOT NULL', name='check_invitation_has_target'),
        sa.ForeignKeyConstraint(['chat_id'], ['chats.id']),
        sa.ForeignKeyConstraint(['receiver_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['sender_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )

    # --- Add nullable columns first ---
    op.add_column('chats', sa.Column('is_open_for_messages', sa.Boolean(), nullable=True))
    op.add_column('users', sa.Column('is_open_for_messages', sa.Boolean(), nullable=True))

    # --- Populate with default values ---
    op.execute("UPDATE chats SET is_open_for_messages = false")
    op.execute("UPDATE users SET is_open_for_messages = false")

    # --- Make columns non-nullable ---
    op.alter_column('chats', 'is_open_for_messages', nullable=False)
    op.alter_column('users', 'is_open_for_messages', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'is_open_for_messages')
    op.drop_column('chats', 'is_open_for_messages')
    op.drop_table('join_requests')
    op.drop_table('invitations')
