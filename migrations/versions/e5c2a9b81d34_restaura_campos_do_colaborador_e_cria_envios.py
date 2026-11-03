"""restaura campos do colaborador e cria envios_rescisao

Revision ID: e5c2a9b81d34
Revises: b424a8a44fda
Create Date: 2026-11-01 14:30:00.000000

A migration b424a8a44fda removeu do colaborador as colunas que a rescisão (TRCT) usa
(salario, data_admissao, situacao, pis_pasep, endereço, ctps, nascimento, nome_mae).
Esta migration coloca de volta só as que ainda NÃO existem, e cria a tabela de envios
de e-mail da rescisão (só se ela ainda não existir).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5c2a9b81d34"
down_revision: Union[str, Sequence[str], None] = "b424a8a44fda"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABELA = "colaboradores"

# (nome, definição). Mesmos tipos da migration f3a8e38b31fb.
COLUNAS = [
    ("salario", lambda: sa.Column("salario", sa.Numeric(10, 2), nullable=False, server_default="0")),
    ("data_admissao", lambda: sa.Column("data_admissao", sa.Date(), nullable=True)),
    ("situacao", lambda: sa.Column("situacao", sa.String(20), nullable=True, server_default="ATIVO")),
    ("pis_pasep", lambda: sa.Column("pis_pasep", sa.String(20), nullable=True)),
    ("logradouro", lambda: sa.Column("logradouro", sa.String(200), nullable=True)),
    ("bairro", lambda: sa.Column("bairro", sa.String(100), nullable=True)),
    ("municipio", lambda: sa.Column("municipio", sa.String(100), nullable=True)),
    ("uf", lambda: sa.Column("uf", sa.String(2), nullable=True)),
    ("cep", lambda: sa.Column("cep", sa.String(10), nullable=True)),
    ("ctps", lambda: sa.Column("ctps", sa.String(50), nullable=True)),
    ("data_nascimento", lambda: sa.Column("data_nascimento", sa.Date(), nullable=True)),
    ("nome_mae", lambda: sa.Column("nome_mae", sa.String(150), nullable=True)),
]


def upgrade() -> None:
    inspetor = sa.inspect(op.get_bind())

    existentes = {c["name"] for c in inspetor.get_columns(TABELA)}
    for nome, definicao in COLUNAS:
        if nome not in existentes:
            op.add_column(TABELA, definicao())

    if "envios_rescisao" not in inspetor.get_table_names():
        op.create_table(
            "envios_rescisao",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("rescisao_id", sa.Integer(), nullable=False),
            sa.Column("destinatario", sa.String(150), nullable=False),
            sa.Column("data", sa.DateTime(), nullable=False),
            sa.Column("sucesso", sa.Boolean(), nullable=False),
            sa.Column("erro", sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(["rescisao_id"], ["rescisoes.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_envios_rescisao_rescisao_id", "envios_rescisao", ["rescisao_id"])


def downgrade() -> None:
    inspetor = sa.inspect(op.get_bind())

    if "envios_rescisao" in inspetor.get_table_names():
        op.drop_table("envios_rescisao")

    existentes = {c["name"] for c in inspetor.get_columns(TABELA)}
    with op.batch_alter_table(TABELA) as lote:
        for nome, _ in reversed(COLUNAS):
            if nome in existentes:
                lote.drop_column(nome)
