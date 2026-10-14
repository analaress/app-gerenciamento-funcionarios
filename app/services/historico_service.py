from sqlalchemy.orm import Session

from app.repositories import historico_repository
from app.schemas.historico import (
    HistoricoCriar,
    ResumoHistorico,
    StatusDocumento,
    TipoDocumento,
)


def listar(
    db: Session,
    busca: str | None = None,
    tipo: TipoDocumento | None = None,
    status: StatusDocumento | None = None,
):
    return historico_repository.listar(
        db, busca, tipo.value if tipo else None, status.value if status else None
    )


def resumo(db: Session) -> ResumoHistorico:
    c = historico_repository.contar_por_status(db)
    return ResumoHistorico(
        pendentes=c.get("PENDENTE", 0),
        gerados=c.get("GERADO", 0) + c.get("ENVIADO", 0),
        enviados=c.get("ENVIADO", 0),
        com_erro=c.get("ERRO_GERACAO", 0) + c.get("ERRO_ENVIO", 0),
        total=sum(c.values()),
    )


def registrar(db: Session, dados: HistoricoCriar):
    return historico_repository.criar(db, dados.model_dump())
