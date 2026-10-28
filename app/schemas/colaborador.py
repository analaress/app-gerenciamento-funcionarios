from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class _ColaboradorBase(BaseModel):
    """Campos comuns. O que é opcional pode ficar em branco no cadastro."""
    nome: str = Field(min_length=2, max_length=150)
    cpf: str = Field(pattern=r"^\d{11}$")
    cargo: str = Field(min_length=2, max_length=100)
    empresa_id: int = Field(gt=0)
    situacao: Literal["ATIVO", "DESLIGADO"] = "ATIVO"
    data_admissao: date | None = None
    pis_pasep: str | None = Field(default=None, max_length=20)
    logradouro: str | None = Field(default=None, max_length=150)
    bairro: str | None = Field(default=None, max_length=100)
    municipio: str | None = Field(default=None, max_length=100)
    uf: str | None = Field(default=None, max_length=2)
    cep: str | None = Field(default=None, max_length=10)
    ctps: str | None = Field(default=None, max_length=40)
    data_nascimento: date | None = None
    nome_mae: str | None = Field(default=None, max_length=150)


class ColaboradorCreate(_ColaboradorBase):
    email: EmailStr
    salario: Decimal = Field(default=Decimal("0"), ge=0, max_digits=10, decimal_places=2)


class ColaboradorResponse(BaseModel):
    """Resposta da API. Sem validação rígida: o que está no banco é devolvido como está."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cpf: str
    email: str
    cargo: str
    empresa_id: int
    salario: Decimal
    situacao: str
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


class EmpresaResumo(BaseModel):
    id: int
    razao_social: str
    cnpj: str


class ColaboradorDetalhe(ColaboradorResponse):
    """Colaborador com a empresa dentro (é o formato que o front espera)."""
    empresa: EmpresaResumo | None = None
