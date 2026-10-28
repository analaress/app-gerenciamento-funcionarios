"""adiciona campos do TRCT ao colaborador

Revision ID: b7d2f4a91c35
Revises: 3084fe173fd8
Create Date: 2026-10-28 00:40:00.000000

Só adiciona as colunas que AINDA NÃO existem (por isso é seguro mesmo que o salario
já tenha sido criado antes pelo scripts/verificar_schema.py).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7d2f4a91c35"
down_revision: Union[str, Sequence[str], None] = "3084fe173fd8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABELA = "colaboradores"

# (nome da coluna, definição). Colunas obrigatórias têm valor padrão, senão o SQLite recusa.
COLUNAS = [
    ("salario", lambda: sa.Column("salario", sa.Numeric(10, 2), nullable=False, server_default="0")),
    ("situacao", lambda: sa.Column("situacao", sa.String(10), nullable=False, server_default="ATIVO")),
    ("data_admissao", lambda: sa.Column("data_admissao", sa.Date(), nullable=True)),
    ("pis_pasep", lambda: sa.Column("pis_pasep", sa.String(20), nullable=True)),
    ("logradouro", lambda: sa.Column("logradouro", sa.String(150), nullable=True)),
    ("bairro", lambda: sa.Column("bairro", sa.String(100), nullable=True)),
    ("municipio", lambda: sa.Column("municipio", sa.String(100), nullable=True)),
    ("uf", lambda: sa.Column("uf", sa.String(2), nullable=True)),
    ("cep", lambda: sa.Column("cep", sa.String(10), nullable=True)),
    ("ctps", lambda: sa.Column("ctps", sa.String(40), nullable=True)),
    ("data_nascimento", lambda: sa.Column("data_nascimento", sa.Date(), nullable=True)),
    ("nome_mae", lambda: sa.Column("nome_mae", sa.String(150), nullable=True)),
]


def _colunas_existentes() -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(TABELA)}


def upgrade() -> None:
    existentes = _colunas_existentes()
    for nome, definicao in COLUNAS:
        if nome not in existentes:
            op.add_column(TABELA, definicao())


def downgrade() -> None:
    existentes = _colunas_existentes()
    with op.batch_alter_table(TABELA) as lote:
        for nome, _ in reversed(COLUNAS):
            if nome in existentes:
                lote.drop_column(nome)
