from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.rescisao import RUBRICAS, StatusRescisao, TipoItem

# Campo 25 do TRCT (causa do afastamento). O código (campo 26) é digitado à parte.
MOTIVOS = [
    "Demissão sem justa causa",
    "Pedido de demissão",
    "Demissão por justa causa",
    "Término de contrato",
    "Extinção normal do contrato de trabalho por prazo determinado",
    "Acordo entre as partes",
]

# Lista das rubricas para a tela de preenchimento (códigos 29 a 53)
VERBAS_SUGERIDAS = [
    {"codigo": cod, "descricao": desc, "tipo": tipo.value}
    for cod, (desc, tipo) in RUBRICAS.items()
]


class ItemEntrada(BaseModel):
    codigo: int
    valor: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    referencia: str | None = Field(default=None, max_length=40)  # ex.: "2/12 avos"
    descricao: str | None = Field(default=None, max_length=120)  # só se quiser trocar o nome padrão

    @field_validator("codigo")
    @classmethod
    def _codigo_valido(cls, codigo: int) -> int:
        if codigo not in RUBRICAS:
            raise ValueError(
                f"Código {codigo} inválido. Use um destes: {sorted(RUBRICAS)} "
                "(46, 54 e 55 são calculados pelo sistema)"
            )
        return codigo


class RescisaoCriar(BaseModel):
    colaborador_id: int
    data_aviso_previo: date | None = None
    data_desligamento: date
    causa_afastamento: str
    codigo_afastamento: str | None = Field(default=None, max_length=10)
    pensao_alimenticia: Decimal | None = Field(default=None, ge=0, le=100)
    categoria_trabalhador: str = "01 - Empregado"
    remuneracao: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    observacoes: str | None = None
    itens: list[ItemEntrada] = Field(min_length=1)

    @field_validator("itens")
    @classmethod
    def _sem_codigos_repetidos(cls, itens: list[ItemEntrada]) -> list[ItemEntrada]:
        codigos = [i.codigo for i in itens]
        if len(codigos) != len(set(codigos)):
            raise ValueError("Cada rubrica (código) só pode aparecer uma vez")
        return itens


class ItemSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: int
    descricao: str
    tipo: TipoItem
    valor: Decimal
    referencia: str | None


class RescisaoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    colaborador_id: int
    empresa_id: int
    data_aviso_previo: date | None
    data_desligamento: date
    causa_afastamento: str
    codigo_afastamento: str | None
    pensao_alimenticia: Decimal | None
    categoria_trabalhador: str
    remuneracao: Decimal
    observacoes: str | None
    total_proventos: Decimal
    total_descontos: Decimal
    total_liquido: Decimal
    status: StatusRescisao
    criado_em: datetime
    itens: list[ItemSaida]


class EnvioSaida(BaseModel):
    """Uma tentativa de envio do PDF por e-mail (sucesso ou falha)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    destinatario: str
    data: datetime
    sucesso: bool
    erro: str | None
