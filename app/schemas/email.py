from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class EmailCreate(BaseModel):
    tipo_documento: str = "recibo"
    assunto: str = Field(min_length=1)
    mensagem: str = Field(min_length=1)


class EmailRegistro(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    colaborador_id: int
    destinatario: str
    assunto: str
    mensagem: str
    status: str
    enviado_em: datetime
    simulado: bool
