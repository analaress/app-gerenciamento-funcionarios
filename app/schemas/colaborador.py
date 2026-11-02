from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ColaboradorCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=150)
    cpf: str = Field(pattern=r"^\d{11}$")
    email: EmailStr
    cargo: str = Field(min_length=2, max_length=100)
    empresa_id: int = Field(gt=0)

    # campos usados na rescisão (opcionais no cadastro)
    salario: Decimal = Field(default=Decimal("0"), ge=0, max_digits=10, decimal_places=2)
    situacao: Literal["ATIVO", "DESLIGADO"] = "ATIVO"
    data_admissao: date | None = None
    pis_pasep: str | None = Field(default=None, max_length=20)
    logradouro: str | None = Field(default=None, max_length=200)
    bairro: str | None = Field(default=None, max_length=100)
    municipio: str | None = Field(default=None, max_length=100)
    uf: str | None = Field(default=None, max_length=2)
    cep: str | None = Field(default=None, max_length=10)
    ctps: str | None = Field(default=None, max_length=50)
    data_nascimento: date | None = None
    nome_mae: str | None = Field(default=None, max_length=150)


class ColaboradorResponse(BaseModel):
    """Resposta da API: devolve o que está no banco, sem validação rígida."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cpf: str
    email: str
    cargo: str
    empresa_id: int
    salario: Decimal = Decimal("0")
    situacao: str | None = None
    data_admissao: date | None = None
    pis_pasep: str | None = None
    logradouro: str | None = None
    bairro: str | None = None
    municipio: str | None = None
    uf: str | None = None
    cep: str | None = None
    ctps: str | None = None
    data_nascimento: date | None = None
    nome_mae: str | None = None
