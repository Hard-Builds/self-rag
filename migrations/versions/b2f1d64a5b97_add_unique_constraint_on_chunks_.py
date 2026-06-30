"""add unique constraint on chunks document_id chunk_index

Revision ID: b2f1d64a5b97
Revises: b1e3f920dc47
Create Date: 2026-06-30 12:35:12.123050

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b2f1d64a5b97'
down_revision: Union[str, None] = 'b1e3f920dc47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        'uq_chunks_document_chunk_index', 'chunks', ['document_id', 'chunk_index']
    )


def downgrade() -> None:
    op.drop_constraint('uq_chunks_document_chunk_index', 'chunks', type_='unique')