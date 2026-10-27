from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.empresa import Empresa
from app.schemas.empresa import EmpresaCriar, EmpresaAtualizar


def criar_empresa(db: Session, dados: EmpresaCriar) -> Empresa:
    empresa = Empresa(**dados.model_dump())

    db.add(empresa)
    db.commit()
    db.refresh(empresa)

    return empresa


def listar_empresas(db: Session) -> list[Empresa]:
    resultado = db.execute(
        select(Empresa)
    )

    return list(resultado.scalars().all())


def buscar_empresa(
    db: Session,
    empresa_id: int
) -> Empresa | None:

    resultado = db.execute(
        select(Empresa).where(Empresa.id == empresa_id)
    )

    return resultado.scalar_one_or_none()


def buscar_por_cnpj(
    db: Session,
    cnpj: str
) -> Empresa | None:

    resultado = db.execute(
        select(Empresa).where(Empresa.cnpj == cnpj)
    )

    return resultado.scalar_one_or_none()


def atualizar_empresa(
    db: Session,
    empresa: Empresa,
    dados: EmpresaAtualizar
) -> Empresa:

    dados_atualizados = dados.model_dump()

    for campo, valor in dados_atualizados.items():
        setattr(empresa, campo, valor)

    db.commit()
    db.refresh(empresa)

    return empresa


def excluir_empresa(
    db: Session,
    empresa: Empresa
) -> None:

    db.delete(empresa)
    db.commit()
