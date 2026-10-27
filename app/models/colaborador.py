from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class Colaborador:
    id: int
    nome: str                 # campo 11 do TRCT
    cpf: str                  # campo 18
    email: str
    empresa_id: int
    cargo: str
    salario: Decimal          # base do campo 21 (remuneração para fins rescisórios)
    data_admissao: date       # campo 22
    situacao: str             # "ATIVO" ou "DESLIGADO"
    pis_pasep: str            # campo 10
    logradouro: str           # campo 12
    bairro: str               # campo 13
    municipio: str            # campo 14
    uf: str                   # campo 15
    cep: str                  # campo 16
    ctps: str                 # campo 17 (nº, série, UF)
    data_nascimento: date     # campo 19
    nome_mae: str             # campo 20
from sqlalchemy import Integer, String
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
