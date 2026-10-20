from app.repositories import historico_repository
from app.schemas.historico import (
    HistoricoCriar,
    ResumoHistorico,
    StatusDocumento,
    TipoDocumento,
)


def listar(
    busca: str | None = None,
    tipo: TipoDocumento | None = None,
    status: StatusDocumento | None = None,
):
    return historico_repository.listar(
        busca, tipo.value if tipo else None, status.value if status else None
    )


def resumo() -> ResumoHistorico:
    c = historico_repository.contar_por_status()
    return ResumoHistorico(
        pendentes=c["PENDENTE"],
        gerados=c["GERADO"] + c["ENVIADO"],
        enviados=c["ENVIADO"],
        com_erro=c["ERRO_GERACAO"] + c["ERRO_ENVIO"],
        total=sum(c.values()),
    )


def registrar(dados: HistoricoCriar):
    return historico_repository.criar(dados.model_dump())