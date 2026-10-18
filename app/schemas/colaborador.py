from pydantic import BaseModel, ConfigDict, Field, field_validator


class ColaboradorBase(BaseModel):
    nome: str = Field(min_length=2)
    email: str = Field(min_length=5)
    cargo: str = Field(min_length=2)
    salario: float = Field(ge=0)
    ativo: bool = True

    @field_validator("email")
    @classmethod
    def validar_email(cls, value: str) -> str:
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("e-mail inválido")
        return value


class ColaboradorCreate(ColaboradorBase):
    pass


class ColaboradorUpdate(ColaboradorBase):
    pass


class Colaborador(ColaboradorBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    empresa_id: int
