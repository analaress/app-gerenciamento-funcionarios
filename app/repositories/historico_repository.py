"""Histórico de documentos guardado no BANCO (antes era uma lista em memória que sumia ao reiniciar).

As funções e o que elas devolvem são os mesmos de antes (dicionários), então o serviço e as rotas
do histórico continuam iguais. Cada função abre e fecha a própria sessão do banco.
"""
from collections import Counter

from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.models.historico_documento import HistoricoDocumento

# campos que entram e saem do histórico (além do id)
CAMPOS = (
    "colaborador_nome",
    "colaborador_cpf",
    "empresa",
    "tipo",
    "status",
    "referencia",
    "data_geracao",
    "data_envio",
    "usuario_responsavel",
)


def _para_dict(registro: HistoricoDocumento) -> dict:
    return {"id": registro.id, **{campo: getattr(registro, campo) for campo in CAMPOS}}


def listar(busca: str | None = None, tipo: str | None = None, status: str | None = None):
    consulta = select(HistoricoDocumento)
    if tipo:
        consulta = consulta.where(HistoricoDocumento.tipo == tipo)
    if status:
        consulta = consulta.where(HistoricoDocumento.status == status)
    consulta = consulta.order_by(HistoricoDocumento.id.desc())  # os mais recentes primeiro

    with SessionLocal() as db:
        registros = [_para_dict(r) for r in db.scalars(consulta).all()]

    if busca:  # a busca por texto é feita aqui para ignorar maiúsculas e acentos como antes
        termo = busca.lower()
        registros = [
            r
            for r in registros
            if termo in f'{r["colaborador_nome"]} {r["colaborador_cpf"]} {r["empresa"]}'.lower()
        ]
    return registros


def contar_por_status() -> Counter:
    with SessionLocal() as db:
        linhas = db.execute(
            select(HistoricoDocumento.status, func.count()).group_by(HistoricoDocumento.status)
        ).all()
    return Counter({status: total for status, total in linhas})


def criar(dados: dict) -> dict:
    with SessionLocal() as db:
        registro = HistoricoDocumento(**{campo: dados.get(campo) for campo in CAMPOS})
        db.add(registro)
        db.commit()
        db.refresh(registro)
        return _para_dict(registro)


def buscar(documento_id: int) -> dict | None:
    with SessionLocal() as db:
        registro = db.get(HistoricoDocumento, documento_id)
        return _para_dict(registro) if registro else None


def atualizar(documento_id: int, **campos) -> dict | None:
    with SessionLocal() as db:
        registro = db.get(HistoricoDocumento, documento_id)
        if registro is None:
            return None
        for campo, valor in campos.items():
            if campo in CAMPOS:
                setattr(registro, campo, valor)
        db.commit()
        db.refresh(registro)
        return _para_dict(registro)
