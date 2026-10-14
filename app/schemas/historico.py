from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict


class TipoDocumento(str, Enum):
    RECIBO = "RECIBO"
    RESCISAO = "RESCISAO"


class StatusDocumento(str, Enum):
    PENDENTE = "PENDENTE"
    EM_CONFERENCIA = "EM_CONFERENCIA"
    GERADO = "GERADO"
    ENVIADO = "ENVIADO"
    ERRO_GERACAO = "ERRO_GERACAO"
    ERRO_ENVIO = "ERRO_ENVIO"


class HistoricoCriar(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    colaborador_nome: str
    colaborador_cpf: str
    empresa: str
    tipo: TipoDocumento
    status: StatusDocumento
    referencia: str | None = None
    data_geracao: date | None = None
    data_envio: date | None = None
    usuario_responsavel: str


class HistoricoDocumentoResposta(HistoricoCriar):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: int


class ResumoHistorico(BaseModel):
    pendentes: int
    gerados: int
    enviados: int
    com_erro: int
    total: int