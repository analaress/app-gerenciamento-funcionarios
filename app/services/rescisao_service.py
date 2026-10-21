from itertools import count
from pathlib import Path

from app.models.rescisao import RUBRICAS, ItemRescisao, Rescisao, StatusRescisao
from app.repositories import colaborador_repository, empresa_repository
from app.schemas.rescisao import MOTIVOS, RescisaoCriar
from app.services import pdf_service
from app.services.calculo_service import calcular_totais

# .../app/services/rescisao_service.py -> raiz do projeto
RAIZ_PROJETO = Path(__file__).resolve().parents[2]
PASTA_PDFS = RAIZ_PROJETO / "storage" / "documents" / "rescisoes"

# "Banco" em memória: as rescisões somem ao reiniciar o servidor
_RESCISOES: dict[int, Rescisao] = {}
_proximo_id_rescisao = count(1)
_proximo_id_item = count(1)


def _validar_causa(causa: str) -> None:
    if causa not in MOTIVOS:
        raise ValueError(f"Causa do afastamento inválida: {causa}")


def _montar_itens(itens_entrada) -> list[ItemRescisao]:
    """Descrição e tipo vêm da tabela de rubricas do TRCT, não do usuário."""
    itens = []
    for i in itens_entrada:
        descricao_padrao, tipo = RUBRICAS[i.codigo]
        itens.append(
            ItemRescisao(
                id=next(_proximo_id_item),
                codigo=i.codigo,
                descricao=i.descricao or descricao_padrao,
                tipo=tipo,
                valor=i.valor,
                referencia=i.referencia,
            )
        )
    return sorted(itens, key=lambda x: x.codigo)


def _aplicar_dados(rescisao: Rescisao, dados: RescisaoCriar, salario) -> None:
    itens = _montar_itens(dados.itens)
    totais = calcular_totais(itens)

    rescisao.data_aviso_previo = dados.data_aviso_previo
    rescisao.data_desligamento = dados.data_desligamento
    rescisao.causa_afastamento = dados.causa_afastamento
    rescisao.codigo_afastamento = dados.codigo_afastamento
    rescisao.pensao_alimenticia = dados.pensao_alimenticia
    rescisao.categoria_trabalhador = dados.categoria_trabalhador
    # sem remuneração informada, usa o salário cadastrado do colaborador
    rescisao.remuneracao = dados.remuneracao if dados.remuneracao is not None else salario
    rescisao.observacoes = dados.observacoes
    rescisao.itens = itens
    rescisao.total_proventos = totais["proventos"]
    rescisao.total_descontos = totais["descontos"]
    rescisao.total_liquido = totais["liquido"]


def criar_rescisao(dados: RescisaoCriar) -> Rescisao:
    _validar_causa(dados.causa_afastamento)

    colaborador = colaborador_repository.obter(dados.colaborador_id)
    if colaborador is None:
        raise LookupError("Colaborador não encontrado")

    rescisao = Rescisao(
        id=next(_proximo_id_rescisao),
        colaborador_id=colaborador.id,
        empresa_id=colaborador.empresa_id,  # preenchido automaticamente
        data_desligamento=dados.data_desligamento,
        causa_afastamento=dados.causa_afastamento,
        remuneracao=colaborador.salario,
        itens=[],
        total_proventos=0,
        total_descontos=0,
        total_liquido=0,
    )
    _aplicar_dados(rescisao, dados, colaborador.salario)
    _RESCISOES[rescisao.id] = rescisao
    return rescisao


def obter_rescisao(rescisao_id: int) -> Rescisao:
    rescisao = _RESCISOES.get(rescisao_id)
    if rescisao is None:
        raise LookupError("Rescisão não encontrada")
    return rescisao


def listar_rescisoes() -> list[Rescisao]:
    return sorted(_RESCISOES.values(), key=lambda r: r.criado_em, reverse=True)


def corrigir_rescisao(rescisao_id: int, dados: RescisaoCriar) -> Rescisao:
    """Correção durante a conferência: só antes de gerar o PDF."""
    rescisao = obter_rescisao(rescisao_id)
    if rescisao.status != StatusRescisao.EM_CONFERENCIA:
        raise ValueError("Só é possível corrigir rescisões em conferência")
    _validar_causa(dados.causa_afastamento)

    colaborador = colaborador_repository.obter(rescisao.colaborador_id)
    _aplicar_dados(rescisao, dados, colaborador.salario)
    return rescisao


def gerar_pdf(rescisao_id: int) -> Rescisao:
    """Gera o PDF da rescisão e muda o status para GERADO (ou ERRO_GERACAO)."""
    rescisao = obter_rescisao(rescisao_id)
    if rescisao.status not in (StatusRescisao.EM_CONFERENCIA, StatusRescisao.ERRO_GERACAO):
        raise ValueError("O PDF só pode ser gerado para rescisões em conferência")

    colaborador = colaborador_repository.obter(rescisao.colaborador_id)
    empresa = empresa_repository.obter(rescisao.empresa_id)
    if colaborador is None or empresa is None:
        raise LookupError("Colaborador ou empresa da rescisão não encontrados")

    destino = PASTA_PDFS / f"rescisao_{rescisao.id}.pdf"
    contexto = {
        "rescisao": rescisao,
        "colaborador": colaborador,
        "empresa": empresa,
        "itens": {item.codigo: item for item in rescisao.itens},  # busca por código
        "rubricas": RUBRICAS,
    }

    try:
        pdf_service.gerar_pdf_rescisao(contexto, destino)
    except Exception as e:
        rescisao.status = StatusRescisao.ERRO_GERACAO
        raise RuntimeError(f"Falha ao gerar o PDF: {e}") from e

    rescisao.caminho_pdf = str(destino)
    rescisao.status = StatusRescisao.GERADO
    return rescisao


def caminho_do_pdf(rescisao_id: int) -> Path:
    rescisao = obter_rescisao(rescisao_id)
    if not rescisao.caminho_pdf or not Path(rescisao.caminho_pdf).exists():
        raise FileNotFoundError("O PDF desta rescisão ainda não foi gerado")
    return Path(rescisao.caminho_pdf)
