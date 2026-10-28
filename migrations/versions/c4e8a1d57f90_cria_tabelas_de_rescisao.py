"""cria tabelas de rescisao

Revision ID: c4e8a1d57f90
Revises: b7d2f4a91c35
Create Date: 2026-10-28 02:30:00.000000

Cria rescisoes, itens_rescisao e envios_rescisao. Só cria a tabela que ainda NÃO existe,
então é seguro rodar mesmo que alguma já tenha sido criada antes.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4e8a1d57f90"
down_revision: Union[str, Sequence[str], None] = "b7d2f4a91c35"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _tabelas_existentes() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    existentes = _tabelas_existentes()

    if "rescisoes" not in existentes:
        op.create_table(
            "rescisoes",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("colaborador_id", sa.Integer(), nullable=False),
            sa.Column("empresa_id", sa.Integer(), nullable=False),
            sa.Column("data_aviso_previo", sa.Date(), nullable=True),
            sa.Column("data_desligamento", sa.Date(), nullable=False),
            sa.Column("causa_afastamento", sa.String(120), nullable=False),
            sa.Column("codigo_afastamento", sa.String(10), nullable=True),
            sa.Column("pensao_alimenticia", sa.Numeric(5, 2), nullable=True),
            sa.Column("categoria_trabalhador", sa.String(60), nullable=False),
            sa.Column("remuneracao", sa.Numeric(12, 2), nullable=False),
            sa.Column("observacoes", sa.Text(), nullable=True),
            sa.Column("total_proventos", sa.Numeric(12, 2), nullable=False),
            sa.Column("total_descontos", sa.Numeric(12, 2), nullable=False),
            sa.Column("total_liquido", sa.Numeric(12, 2), nullable=False),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("caminho_pdf", sa.String(255), nullable=True),
            sa.Column("criado_em", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["colaborador_id"], ["colaboradores.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_rescisoes_colaborador_id", "rescisoes", ["colaborador_id"])

    if "itens_rescisao" not in existentes:
        op.create_table(
            "itens_rescisao",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("rescisao_id", sa.Integer(), nullable=False),
            sa.Column("codigo", sa.Integer(), nullable=False),
            sa.Column("descricao", sa.String(120), nullable=False),
            sa.Column("tipo", sa.String(12), nullable=False),
            sa.Column("valor", sa.Numeric(12, 2), nullable=False),
            sa.Column("referencia", sa.String(40), nullable=True),
            sa.ForeignKeyConstraint(["rescisao_id"], ["rescisoes.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_itens_rescisao_rescisao_id", "itens_rescisao", ["rescisao_id"])

    if "envios_rescisao" not in existentes:
        op.create_table(
            "envios_rescisao",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("rescisao_id", sa.Integer(), nullable=False),
            sa.Column("destinatario", sa.String(150), nullable=False),
            sa.Column("data", sa.DateTime(), nullable=False),
            sa.Column("sucesso", sa.Boolean(), nullable=False),
            sa.Column("erro", sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(["rescisao_id"], ["rescisoes.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_envios_rescisao_rescisao_id", "envios_rescisao", ["rescisao_id"])


def downgrade() -> None:
    existentes = _tabelas_existentes()
    # ordem inversa: primeiro as tabelas que dependem de 'rescisoes'
    for nome in ("envios_rescisao", "itens_rescisao", "rescisoes"):
        if nome in existentes:
            op.drop_table(nome)
