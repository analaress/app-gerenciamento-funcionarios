from sqlalchemy.orm import Session

from app.repositories import empresa_repository
from app.schemas.empresa import EmpresaCriar, EmpresaAtualizar


def criar_empresa(
    db: Session,
    dados: EmpresaCriar
):
    empresa_existente = empresa_repository.buscar_por_cnpj(
        db,
        dados.cnpj
    )

    if empresa_existente:
        raise ValueError(
            "Já existe uma empresa cadastrada com este CNPJ."
        )

    return empresa_repository.criar_empresa(
        db,
        dados
    )


def listar_empresas(db: Session):
    return empresa_repository.listar_empresas(db)


def buscar_empresa(
    db: Session,
    empresa_id: int
):
    empresa = empresa_repository.buscar_empresa(
        db,
        empresa_id
    )

    if empresa is None:
        raise ValueError("Empresa não encontrada.")

    return empresa


def atualizar_empresa(
    db: Session,
    empresa_id: int,
    dados: EmpresaAtualizar
):
    empresa = empresa_repository.buscar_empresa(
        db,
        empresa_id
    )

    if empresa is None:
        raise ValueError("Empresa não encontrada.")

    return empresa_repository.atualizar_empresa(
        db,
        empresa,
        dados
    )


def excluir_empresa(
    db: Session,
    empresa_id: int
):
    empresa = empresa_repository.buscar_empresa(
        db,
        empresa_id
    )

    if empresa is None:
        raise ValueError("Empresa não encontrada.")

    empresa_repository.excluir_empresa(
        db,
        empresa
    )
