
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.colaborador import (
    ColaboradorCreate,
    ColaboradorResponse
)
from app.services import colaborador_service


router = APIRouter(
    prefix="/colaboradores",
    tags=["Colaboradores"]
)


@router.post(
    "/",
    response_model=ColaboradorResponse,
    status_code=201
)
def cadastrar_colaborador(
    dados: ColaboradorCreate,
    db: Session = Depends(get_db)
):
    return colaborador_service.cadastrar(db, dados)


@router.get(
    "/",
    response_model=list[ColaboradorResponse]
)
def listar_colaboradores(
    db: Session = Depends(get_db)
):
    return colaborador_service.listar(db)


@router.get(
    "/{colaborador_id}",
    response_model=ColaboradorResponse
)
def selecionar_colaborador(
    colaborador_id: int,
    db: Session = Depends(get_db)
):
    return colaborador_service.selecionar(
        db, colaborador_id
    )
