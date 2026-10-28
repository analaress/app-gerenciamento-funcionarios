from fastapi import HTTPException

from app.repositories.colaborador_repository import ColaboradorRepository
from app.repositories.empresa_repository import EmpresaRepository


class ColaboradorService:
    def __init__(self, repository=None, empresas=None):
        self.repository = repository or ColaboradorRepository()
        self.empresas = empresas or EmpresaRepository()

    def listar_por_empresa(self, empresa_id):
        if not self.empresas.get_by_id(empresa_id): raise HTTPException(404, "Empresa não encontrada")
        return self.repository.list_by_empresa(empresa_id)

    def buscar(self, colaborador_id):
        item = self.repository.get_by_id(colaborador_id)
        if not item: raise HTTPException(404, "Colaborador não encontrado")
        return item

    def criar(self, empresa_id, data):
        if not self.empresas.get_by_id(empresa_id): raise HTTPException(404, "Empresa não encontrada")
        return self.repository.create({**data.model_dump(), "empresa_id": empresa_id})

    def atualizar(self, colaborador_id, data):
        item = self.buscar(colaborador_id)
        if not self.empresas.get_by_id(item["empresa_id"]): raise HTTPException(404, "Empresa não encontrada")
        return self.repository.update(colaborador_id, data.model_dump())

    def excluir(self, colaborador_id):
        self.buscar(colaborador_id)
        self.repository.delete(colaborador_id)
