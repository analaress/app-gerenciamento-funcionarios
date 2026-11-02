from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Colaborador(Base):
    __tablename__ = "colaboradores"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    nome: Mapped[str] = mapped_column(
        String(150), nullable=False
    )

    cpf: Mapped[str] = mapped_column(
        String(11), unique=True, nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(150), nullable=False
    )

    cargo: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    empresa_id: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    # --- campos que a rescisão (TRCT) usa; as colunas vêm da migration e5c2a9b81d34 ---
    salario: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0, server_default="0"
    )  # base do campo 21 (remuneração para fins rescisórios)
    data_admissao: Mapped[date | None] = mapped_column(Date, nullable=True)  # campo 22
    situacao: Mapped[str | None] = mapped_column(
        String(20), nullable=True, default="ATIVO", server_default="ATIVO"
    )  # "ATIVO" ou "DESLIGADO"
    pis_pasep: Mapped[str | None] = mapped_column(String(20), nullable=True)  # campo 10
    logradouro: Mapped[str | None] = mapped_column(String(200), nullable=True)  # campo 12
    bairro: Mapped[str | None] = mapped_column(String(100), nullable=True)  # campo 13
    municipio: Mapped[str | None] = mapped_column(String(100), nullable=True)  # campo 14
    uf: Mapped[str | None] = mapped_column(String(2), nullable=True)  # campo 15
    cep: Mapped[str | None] = mapped_column(String(10), nullable=True)  # campo 16
    ctps: Mapped[str | None] = mapped_column(String(50), nullable=True)  # campo 17 (nº, série, UF)
    data_nascimento: Mapped[date | None] = mapped_column(Date, nullable=True)  # campo 19
    nome_mae: Mapped[str | None] = mapped_column(String(150), nullable=True)  # campo 20
