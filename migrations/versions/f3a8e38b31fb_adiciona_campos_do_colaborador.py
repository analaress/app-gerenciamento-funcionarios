"""adiciona campos do colaborador"""
from alembic import op
import sqlalchemy as sa

revision = "f3a8e38b31fb"
down_revision = "3084fe173fd8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("colaboradores", sa.Column("salario", sa.Numeric(10, 2), nullable=False, server_default="0"))
    op.add_column("colaboradores", sa.Column("data_admissao", sa.Date(), nullable=True))
    op.add_column("colaboradores", sa.Column("situacao", sa.String(20), nullable=True))
    op.add_column("colaboradores", sa.Column("pis_pasep", sa.String(20), nullable=True))
    op.add_column("colaboradores", sa.Column("logradouro", sa.String(200), nullable=True))
    op.add_column("colaboradores", sa.Column("bairro", sa.String(100), nullable=True))
    op.add_column("colaboradores", sa.Column("municipio", sa.String(100), nullable=True))
    op.add_column("colaboradores", sa.Column("uf", sa.String(2), nullable=True))
    op.add_column("colaboradores", sa.Column("cep", sa.String(10), nullable=True))
    op.add_column("colaboradores", sa.Column("ctps", sa.String(50), nullable=True))
    op.add_column("colaboradores", sa.Column("data_nascimento", sa.Date(), nullable=True))
    op.add_column("colaboradores", sa.Column("nome_mae", sa.String(150), nullable=True))


def downgrade() -> None:
    for column in ("nome_mae", "data_nascimento", "ctps", "cep", "uf", "municipio", "bairro", "logradouro", "pis_pasep", "situacao", "data_admissao", "salario"):
        op.drop_column("colaboradores", column)
