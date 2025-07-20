"""join_request_type

Revision ID: a7029369908b
Revises: f7915e6b93c5
Create Date: 2025-07-08 16:43:10.296348

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7029369908b'
down_revision: Union[str, None] = 'f7915e6b93c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Сначала создать enum тип вручную
    join_request_type_enum = sa.Enum('USER', 'GROUP', name='joinrequesttype')
    join_request_type_enum.create(op.get_bind())

    # Потом использовать его
    op.add_column('join_requests', sa.Column('join_request_type', join_request_type_enum, nullable=False))
    op.add_column('join_requests', sa.Column('group_id', sa.Integer(), nullable=True))
    op.drop_constraint('join_requests_chat_id_fkey', 'join_requests', type_='foreignkey')
    op.create_foreign_key(None, 'join_requests', 'chats', ['group_id'], ['id'])
    op.drop_column('join_requests', 'chat_id')

def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('join_requests', sa.Column('chat_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'join_requests', type_='foreignkey')
    op.create_foreign_key('join_requests_chat_id_fkey', 'join_requests', 'chats', ['chat_id'], ['id'])
    op.drop_column('join_requests', 'group_id')
    op.drop_column('join_requests', 'join_request_type')

    # Удалить тип из базы
    sa.Enum(name='joinrequesttype').drop(op.get_bind())
