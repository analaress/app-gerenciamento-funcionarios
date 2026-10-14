from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.historico_documento import HistoricoDocumento


def listar(db: Session, busca: str | None, tipo: str | None, status: str | None):
    consulta = select(HistoricoDocumento).order_by(HistoricoDocumento.id.desc())
    if busca:
        termo = f"%{busca}%"
        consulta = consulta.where(
            or_(
                HistoricoDocumento.colaborador_nome.ilike(termo),
                HistoricoDocumento.colaborador_cpf.ilike(termo),
                HistoricoDocumento.empresa.ilike(termo),
            )
        )
    if tipo:
        consulta = consulta.where(HistoricoDocumento.tipo == tipo)
    if status:
        consulta = consulta.where(HistoricoDocumento.status == status)
    return list(db.scalars(consulta))


def contar_por_status(db: Session) -> dict[str, int]:
    linhas = db.execute(
        select(HistoricoDocumento.status, func.count()).group_by(HistoricoDocumento.status)
    )
    return {status: total for status, total in linhas}


def criar(db: Session, dados: dict) -> HistoricoDocumento:
    registro = HistoricoDocumento(**dados)
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro
