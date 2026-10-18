from fastapi import HTTPException

from app.repositories.colaborador_repository import ColaboradorRepository
from app.repositories.empresa_repository import EmpresaRepository
from app.schemas.empresa import EmpresaCreate, EmpresaUpdate


class EmpresaService:
    def __init__(self, repository=None, colaboradores=None):
        self.repository = repository or EmpresaRepository()
        self.colaboradores = colaboradores or ColaboradorRepository()

    def listar(self): return self.repository.list()

    def buscar(self, empresa_id):
        item = self.repository.get_by_id(empresa_id)
        if not item: raise HTTPException(404, "Empresa não encontrada")
        return item

    def criar(self, data: EmpresaCreate): return self.repository.create(data.model_dump())

    def atualizar(self, empresa_id, data: EmpresaUpdate):
        self.buscar(empresa_id)
        return self.repository.update(empresa_id, data.model_dump())

    def excluir(self, empresa_id):
        self.buscar(empresa_id)
        if self.colaboradores.list_by_empresa(empresa_id):
            raise HTTPException(409, "Empresa possui colaboradores")
        self.repository.delete(empresa_id)
