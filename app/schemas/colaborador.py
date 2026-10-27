from pydantic import BaseModel, ConfigDict, Field, EmailStr

class ColaboradorCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=150)
    cpf: str = Field(pattern=r"^\d{11}$")
    email: EmailStr
    cargo: str = Field(min_length=2, max_length=100)
    empresa_id: int = Field(gt=0)

class ColaboradorResponse(ColaboradorCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)