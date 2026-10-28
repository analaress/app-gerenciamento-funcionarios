from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.colaborador import Colaborador


def criar(db: Session, dados: dict):
    colaborador = Colaborador(**dados)

    db.add(colaborador)
    db.commit()
    db.refresh(colaborador)

    return colaborador

def listar(db: Session):
    return db.scalars(
        select(Colaborador).order_by(Colaborador.id)
    ).all()


def buscar_por_id(db: Session, colaborador_id: int):
    return db.get(Colaborador, colaborador_id)

def buscar_por_cpf(db: Session, cpf: str):
    return db.scalar(
        select(Colaborador).where(
            Colaborador.cpf == cpf
        )
    )
