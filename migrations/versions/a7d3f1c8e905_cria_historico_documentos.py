"""cria historico_documentos

Revision ID: a7d3f1c8e905
Revises: e5c2a9b81d34
Create Date: 2026-11-01 19:30:00.000000

O histórico de documentos (recibos e rescisões) passa a ficar no banco. Só cria a tabela
se ela ainda não existir.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7d3f1c8e905"
down_revision: Union[str, Sequence[str], None] = "e5c2a9b81d34"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if "historico_documentos" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "historico_documentos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("colaborador_nome", sa.String(150), nullable=False),
        sa.Column("colaborador_cpf", sa.String(20), nullable=False),
        sa.Column("empresa", sa.String(150), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("referencia", sa.String(100), nullable=True),
        sa.Column("data_geracao", sa.Date(), nullable=True),
        sa.Column("data_envio", sa.Date(), nullable=True),
        sa.Column("usuario_responsavel", sa.String(150), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_historico_documentos_referencia", "historico_documentos", ["referencia"])


def downgrade() -> None:
    if "historico_documentos" in sa.inspect(op.get_bind()).get_table_names():
        op.drop_table("historico_documentos")
