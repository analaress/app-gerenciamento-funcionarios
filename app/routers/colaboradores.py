from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories import empresa_repository
from app.schemas.colaborador import (
    ColaboradorCreate,
    ColaboradorDetalhe,
    ColaboradorResponse,
    EmpresaResumo,
)
from app.services import colaborador_service

router = APIRouter(prefix="/colaboradores", tags=["Colaboradores"])


def _detalhe(colaborador) -> ColaboradorDetalhe:
    """Colaborador do banco + dados da empresa.

    A empresa ainda não é uma tabela: vem do empresa_repository (Faker).
    Quando existir a tabela, só esta função muda.
    """
    empresa = empresa_repository.obter(colaborador.empresa_id)
    resumo = (
        EmpresaResumo(id=empresa.id, razao_social=empresa.razao_social, cnpj=empresa.cnpj)
        if empresa
        else None
    )
    return ColaboradorDetalhe.model_validate(colaborador).model_copy(update={"empresa": resumo})


@router.post("/", response_model=ColaboradorResponse, status_code=201)
def cadastrar_colaborador(dados: ColaboradorCreate, db: Session = Depends(get_db)):
    return colaborador_service.cadastrar(db, dados)


@router.get("/", response_model=list[ColaboradorDetalhe])
def listar_colaboradores(db: Session = Depends(get_db)):
    return [_detalhe(c) for c in colaborador_service.listar(db)]


@router.get("/{colaborador_id}", response_model=ColaboradorDetalhe)
def selecionar_colaborador(colaborador_id: int, db: Session = Depends(get_db)):
    return _detalhe(colaborador_service.selecionar(db, colaborador_id))
