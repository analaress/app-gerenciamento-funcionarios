from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from app.repositories import colaborador_repository, empresa_repository

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
