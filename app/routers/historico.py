from fastapi import APIRouter

from app.schemas.historico import (
    HistoricoCriar,
    HistoricoDocumentoResposta,
    ResumoHistorico,
    StatusDocumento,
    TipoDocumento,
)
from app.services import historico_service

router = APIRouter(prefix="/historico", tags=["Histórico"])


@router.get("", response_model=list[HistoricoDocumentoResposta])
def listar(
    busca: str | None = None,
    tipo: TipoDocumento | None = None,
    status: StatusDocumento | None = None,
):
    return historico_service.listar(busca, tipo, status)


@router.get("/resumo", response_model=ResumoHistorico)
def resumo():
    return historico_service.resumo()


@router.post("", response_model=HistoricoDocumentoResposta, status_code=201)
def registrar(dados: HistoricoCriar):
    return historico_service.registrar(dados)