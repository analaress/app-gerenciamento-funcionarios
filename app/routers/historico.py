from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
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
    db: Session = Depends(get_db),
):
    return historico_service.listar(db, busca, tipo, status)


@router.get("/resumo", response_model=ResumoHistorico)
def resumo(db: Session = Depends(get_db)):
    return historico_service.resumo(db)


@router.post("", response_model=HistoricoDocumentoResposta, status_code=201)
def registrar(dados: HistoricoCriar, db: Session = Depends(get_db)):
    return historico_service.registrar(db, dados)
