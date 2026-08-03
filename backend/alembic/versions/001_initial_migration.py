"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2026-05-18 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create contracts table
    op.create_table(
        'contracts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=1000), nullable=False),
        sa.Column('contract_type', sa.String(length=100), nullable=True),
        sa.Column('parties', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('effective_date', sa.Date(), nullable=True),
        sa.Column('expiration_date', sa.Date(), nullable=True),
        sa.Column('full_text', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('processing_started_at', sa.DateTime(), nullable=True),
        sa.Column('processing_completed_at', sa.DateTime(), nullable=True),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contracts_contract_type'), 'contracts', ['contract_type'], unique=False)
    op.create_index(op.f('ix_contracts_status'), 'contracts', ['status'], unique=False)
    op.create_index(op.f('ix_contracts_title'), 'contracts', ['title'], unique=False)

    # Create clauses table
    op.create_table(
        'clauses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contract_id', sa.Integer(), nullable=False),
        sa.Column('clause_number', sa.String(length=50), nullable=True),
        sa.Column('clause_title', sa.String(length=500), nullable=True),
        sa.Column('clause_type', sa.String(length=100), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('risk_level', sa.String(length=20), nullable=True),
        sa.Column('importance_score', sa.Float(), nullable=True),
        sa.Column('extraction_confidence', sa.Float(), nullable=True),
        sa.Column('extraction_method', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_clauses_clause_type'), 'clauses', ['clause_type'], unique=False)
    op.create_index(op.f('ix_clauses_contract_id'), 'clauses', ['contract_id'], unique=False)
    op.create_index(op.f('ix_clauses_risk_level'), 'clauses', ['risk_level'], unique=False)

    # Create document_sections table
    op.create_table(
        'document_sections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contract_id', sa.Integer(), nullable=False),
        sa.Column('parent_section_id', sa.Integer(), nullable=True),
        sa.Column('section_number', sa.String(length=50), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_section_id'], ['document_sections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_sections_contract_id'), 'document_sections', ['contract_id'], unique=False)
    op.create_index(op.f('ix_document_sections_parent_section_id'), 'document_sections', ['parent_section_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_document_sections_parent_section_id'), table_name='document_sections')
    op.drop_index(op.f('ix_document_sections_contract_id'), table_name='document_sections')
    op.drop_table('document_sections')
    
    op.drop_index(op.f('ix_clauses_risk_level'), table_name='clauses')
    op.drop_index(op.f('ix_clauses_contract_id'), table_name='clauses')
    op.drop_index(op.f('ix_clauses_clause_type'), table_name='clauses')
    op.drop_table('clauses')
    
    op.drop_index(op.f('ix_contracts_title'), table_name='contracts')
    op.drop_index(op.f('ix_contracts_status'), table_name='contracts')
    op.drop_index(op.f('ix_contracts_contract_type'), table_name='contracts')
    op.drop_table('contracts')

# Made with Bob
