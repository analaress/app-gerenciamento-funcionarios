from fastapi import APIRouter, status
from app.schemas.colaborador import ColaboradorCreate, ColaboradorUpdate
from app.services.colaborador_service import ColaboradorService

router = APIRouter(prefix="/colaboradores", tags=["colaboradores"])
service = ColaboradorService()

@router.get("/{colaborador_id}")
def buscar(colaborador_id: int): return service.buscar(colaborador_id)
@router.put("/{colaborador_id}")
def atualizar(colaborador_id: int, data: ColaboradorUpdate): return service.atualizar(colaborador_id, data)
@router.delete("/{colaborador_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(colaborador_id: int): service.excluir(colaborador_id)
@router.get("/empresa/{empresa_id}")
def listar_por_empresa(empresa_id: int): return service.listar_por_empresa(empresa_id)
