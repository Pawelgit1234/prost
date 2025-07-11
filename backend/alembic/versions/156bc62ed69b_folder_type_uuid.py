"""folder type, uuid

Revision ID: 156bc62ed69b
Revises: aaac7baebc8c
Create Date: 2025-06-07 07:42:04.467192

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '156bc62ed69b'
down_revision: Union[str, None] = 'aaac7baebc8c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    folder_type_enum = sa.Enum('CUSTOM', 'ALL', 'CHATS', 'GROUPS', 'NEW', name='foldertype')
    folder_type_enum.create(op.get_bind(), checkfirst=True)
    op.add_column('folders', sa.Column('folder_type', folder_type_enum, nullable=False))
    op.create_unique_constraint(None, 'folders', ['uuid'])
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'folders', type_='unique')
    op.drop_column('folders', 'folder_type')

    folder_type_enum = sa.Enum('CUSTOM', 'ALL', 'CHATS', 'GROUPS', 'NEW', name='foldertype')
    folder_type_enum.drop(op.get_bind(), checkfirst=True)
    # ### end Alembic commands ###