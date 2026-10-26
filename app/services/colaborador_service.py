
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.repositories import colaborador_repository as repo
from app.schemas.colaborador import ColaboradorCreate


def cadastrar(db: Session, dados: ColaboradorCreate):
    existente = repo.buscar_por_cpf(db, dados.cpf)

    if existente:
        raise HTTPException(
            status_code=409,
            detail="CPF já cadastrado"
        )

    try:
        return repo.criar(db, dados.model_dump())
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Conflito ao cadastrar colaborador"
        )


def listar(db: Session):
    return repo.listar(db)

def selecionar(db: Session, colaborador_id: int):
    colaborador = repo.buscar_por_id(
        db, colaborador_id
    )

    if not colaborador:
        raise HTTPException(
            status_code=404,
            detail="Colaborador não encontrado"
        )

    return colaborador
