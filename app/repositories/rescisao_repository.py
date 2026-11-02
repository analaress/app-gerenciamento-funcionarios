from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.rescisao import EnvioRescisao, Rescisao


def adicionar(db: Session, rescisao: Rescisao) -> Rescisao:
    """Grava uma rescisão nova."""
    db.add(rescisao)
    db.commit()
    db.refresh(rescisao)
    return rescisao


def salvar(db: Session, rescisao: Rescisao) -> Rescisao:
    """Grava as alterações de uma rescisão que já está na sessão."""
    db.commit()
    db.refresh(rescisao)
    return rescisao


def buscar_por_id(db: Session, rescisao_id: int) -> Rescisao | None:
    return db.get(Rescisao, rescisao_id)


def listar(db: Session) -> list[Rescisao]:
    return list(db.scalars(select(Rescisao).order_by(Rescisao.id)).all())


def registrar_envio(
    db: Session, rescisao_id: int, destinatario: str, sucesso: bool, erro: str | None = None
) -> EnvioRescisao:
    """Registra uma tentativa de envio. O commit também grava o status novo da rescisão."""
    envio = EnvioRescisao(
        rescisao_id=rescisao_id, destinatario=destinatario, sucesso=sucesso, erro=erro
    )
    db.add(envio)
    db.commit()
    db.refresh(envio)
    return envio


def listar_envios(db: Session, rescisao_id: int) -> list[EnvioRescisao]:
    return list(
        db.scalars(
            select(EnvioRescisao)
            .where(EnvioRescisao.rescisao_id == rescisao_id)
            .order_by(EnvioRescisao.id)
        ).all()
    )


def buscar_por_colaborador(db: Session, colaborador_id: int) -> Rescisao | None:
    """A primeira rescisão do colaborador (cada colaborador só pode ter uma)."""
    return db.scalars(
        select(Rescisao).where(Rescisao.colaborador_id == colaborador_id).order_by(Rescisao.id)
    ).first()


def marcar_colaborador_desligado(db: Session, colaborador) -> None:
    """Muda a situação do colaborador para DESLIGADO (depois disso ele não recebe mais documentos)."""
    colaborador.situacao = "DESLIGADO"
    db.add(colaborador)
    db.commit()
    db.refresh(colaborador)
