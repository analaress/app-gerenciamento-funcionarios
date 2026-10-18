from pydantic import BaseModel, ConfigDict, Field


class EmpresaBase(BaseModel):
    nome: str = Field(min_length=2)
    cnpj: str = Field(min_length=5)


class EmpresaCreate(EmpresaBase):
    pass


class EmpresaUpdate(EmpresaBase):
    pass


class Empresa(EmpresaBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
