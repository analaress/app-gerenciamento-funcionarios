from fastapi import APIRouter, status
from app.schemas.empresa import EmpresaCreate, EmpresaUpdate
from app.services.empresa_service import EmpresaService

router = APIRouter(prefix="/empresas", tags=["empresas"])
service = EmpresaService()

@router.get("")
def listar(): return service.listar()
@router.post("", status_code=status.HTTP_201_CREATED)
def criar(data: EmpresaCreate): return service.criar(data)
@router.get("/{empresa_id}")
def buscar(empresa_id: int): return service.buscar(empresa_id)
@router.put("/{empresa_id}")
def atualizar(empresa_id: int, data: EmpresaUpdate): return service.atualizar(empresa_id, data)
@router.delete("/{empresa_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(empresa_id: int): service.excluir(empresa_id)
