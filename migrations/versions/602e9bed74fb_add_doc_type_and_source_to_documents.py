"""add doc_type and source to documents

Revision ID: 602e9bed74fb
Revises: b2f1d64a5b97
Create Date: 2026-06-30 14:25:55.442043

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '602e9bed74fb'
down_revision: Union[str, None] = 'b2f1d64a5b97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('documents', sa.Column('doc_type', sa.String(), nullable=True))
    op.add_column('documents', sa.Column('source', sa.String(), nullable=True))
    op.create_index('ix_documents_doc_type', 'documents', ['doc_type'], unique=False)
    op.create_index('ix_documents_source', 'documents', ['source'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_documents_source', table_name='documents')
    op.drop_index('ix_documents_doc_type', table_name='documents')
    op.drop_column('documents', 'source')
    op.drop_column('documents', 'doc_type')
