from dataclasses import asdict
from fastapi import APIRouter, HTTPException
from app.repositories import colaborador_repository, empresa_repository
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.colaborador import (
    ColaboradorCreate,
    ColaboradorResponse
)
from app.services import colaborador_service

router = APIRouter(prefix="/colaboradores", tags=["Colaboradores"])


def _com_empresa(colaborador) -> dict:
    """Colaborador + dados da empresa (o front precisa do nome da empresa)."""
    empresa = empresa_repository.obter(colaborador.empresa_id)
    return {**asdict(colaborador), "empresa": asdict(empresa) if empresa else None}


@router.get("/")
def listar(nome: str | None = None, empresa_id: int | None = None):
    return [_com_empresa(c) for c in colaborador_repository.listar(nome, empresa_id)]


@router.get("/{colaborador_id}")
def detalhar(colaborador_id: int):
    colaborador = colaborador_repository.obter(colaborador_id)
    if colaborador is None:
        raise HTTPException(status_code=404, detail="Colaborador não encontrado")
    return _com_empresa(colaborador)



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
