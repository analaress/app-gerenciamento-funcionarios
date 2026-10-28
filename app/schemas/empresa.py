from pydantic import BaseModel, ConfigDict


class EmpresaBase(BaseModel):
    razao_social: str
    nome_fantasia: str
    cnpj: str

    email: str
    telefone: str

    cep: str | None = None
    logradouro: str | None = None
    numero: str | None = None
    complemento: str | None = None
    bairro: str | None = None
    cidade: str | None = None
    estado: str | None = None

    representante_legal: str | None = None


class EmpresaCriar(EmpresaBase):
    pass


class EmpresaAtualizar(EmpresaBase):
    pass


class EmpresaResposta(EmpresaBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
