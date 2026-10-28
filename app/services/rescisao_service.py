
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.rescisao import Rescisao, StatusRescisao, RUBRICAS
from app.schemas.rescisao import MOTIVOS, RescisaoCriar
from app.services.calculo_service import calcular_totais


def criar(db: Session, dados: RescisaoCriar) -> Rescisao:
    if dados.causa_afastamento not in MOTIVOS:
        raise ValueError("Causa do afastamento inválida")

    itens = []
    for item in dados.itens:
        descricao, tipo = RUBRICAS[item.codigo]
        itens.append({
            "codigo": item.codigo,
            "descricao": item.descricao or descricao,
            "tipo": tipo.value,
            "valor": str(item.valor),
            "referencia": item.referencia,
        })

    totais = calcular_totais(dados.itens)
    registro = Rescisao(
        colaborador_id=dados.colaborador_id,
        empresa_id=0,
        data_aviso_previo=dados.data_aviso_previo,
        data_desligamento=dados.data_desligamento,
        causa_afastamento=dados.causa_afastamento,
        codigo_afastamento=dados.codigo_afastamento,
        pensao_alimenticia=dados.pensao_alimenticia,
        categoria_trabalhador=dados.categoria_trabalhador,
        remuneracao=dados.remuneracao or Decimal("0"),
        observacoes=dados.observacoes,
        total_proventos=totais["proventos"],
        total_descontos=totais["descontos"],
        total_liquido=totais["liquido"],
        status=StatusRescisao.EM_CONFERENCIA.value,
        itens=itens,
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro


def listar(db: Session) -> list[Rescisao]:
    return list(db.scalars(select(Rescisao).order_by(Rescisao.id)).all())


def obter(db: Session, rescisao_id: int) -> Rescisao:
    registro = db.get(Rescisao, rescisao_id)
    if registro is None:
        raise LookupError("Rescisão não encontrada")
    return registro
