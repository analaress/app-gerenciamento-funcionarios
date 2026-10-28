from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.empresa import (
    EmpresaCriar,
    EmpresaAtualizar,
    EmpresaResposta
)
from app.services import empresa_service


router = APIRouter(
    prefix="/empresas",
    tags=["Empresas"]
)


@router.post(
    "",
    response_model=EmpresaResposta,
    status_code=201
)
def criar_empresa(
    dados: EmpresaCriar,
    db: Session = Depends(get_db)
):
    try:
        return empresa_service.criar_empresa(
            db,
            dados
        )

    except ValueError as erro:
        raise HTTPException(
            status_code=400,
            detail=str(erro)
        )


@router.get(
    "",
    response_model=list[EmpresaResposta]
)
def listar_empresas(
    db: Session = Depends(get_db)
):
    return empresa_service.listar_empresas(db)


@router.get(
    "/{empresa_id}",
    response_model=EmpresaResposta
)
def buscar_empresa(
    empresa_id: int,
    db: Session = Depends(get_db)
):
    try:
        return empresa_service.buscar_empresa(
            db,
            empresa_id
        )

    except ValueError as erro:
        raise HTTPException(
            status_code=404,
            detail=str(erro)
        )


@router.put(
    "/{empresa_id}",
    response_model=EmpresaResposta
)
def atualizar_empresa(
    empresa_id: int,
    dados: EmpresaAtualizar,
    db: Session = Depends(get_db)
):
    try:
        return empresa_service.atualizar_empresa(
            db,
            empresa_id,
            dados
        )

    except ValueError as erro:
        raise HTTPException(
            status_code=404,
            detail=str(erro)
        )


@router.delete(
    "/{empresa_id}",
    status_code=204
)
def excluir_empresa(
    empresa_id: int,
    db: Session = Depends(get_db)
):
    try:
        empresa_service.excluir_empresa(
            db,
            empresa_id
        )

    except ValueError as erro:
        raise HTTPException(
            status_code=404,
            detail=str(erro)
        )
