from pathlib import Path

from sqlalchemy.orm import Session

from app.models.rescisao import RUBRICAS, ItemRescisao, Rescisao, StatusRescisao
from app.repositories import colaborador_repository, empresa_repository, rescisao_repository
from app.schemas.rescisao import MOTIVOS, RescisaoCriar
from app.services import email_service, pdf_service
from app.services.calculo_service import calcular_totais

# .../app/services/rescisao_service.py -> raiz do projeto
RAIZ_PROJETO = Path(__file__).resolve().parents[2]
PASTA_PDFS = RAIZ_PROJETO / "storage" / "documents" / "rescisoes"

# Em quais situações ainda dá para corrigir os dados (a correção volta para EM_CONFERENCIA)
_STATUS_CORRIGIVEIS = (
    StatusRescisao.EM_CONFERENCIA,
    StatusRescisao.GERADO,
    StatusRescisao.ENVIADO,
    StatusRescisao.ERRO_GERACAO,
    StatusRescisao.ERRO_ENVIO,
)

# Em quais situações o PDF existe e pode ser enviado
_STATUS_ENVIAVEIS = (
    StatusRescisao.GERADO,
    StatusRescisao.ENVIADO,
    StatusRescisao.ERRO_ENVIO,
)


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
    rescisao.itens = itens  # os itens antigos, se houver, saem (delete-orphan) e os novos entram
    rescisao.total_proventos = totais["proventos"]
    rescisao.total_descontos = totais["descontos"]
    rescisao.total_liquido = totais["liquido"]


def criar_rescisao(db: Session, dados: RescisaoCriar) -> Rescisao:
    _validar_causa(dados.causa_afastamento)

    colaborador = colaborador_repository.buscar_por_id(db, dados.colaborador_id)
    if colaborador is None:
        raise LookupError("Colaborador não encontrado")

    rescisao = Rescisao(
        colaborador_id=colaborador.id,
        empresa_id=colaborador.empresa_id,  # preenchido automaticamente
        data_desligamento=dados.data_desligamento,
        causa_afastamento=dados.causa_afastamento,
        remuneracao=colaborador.salario,
        total_proventos=0,
        total_descontos=0,
        total_liquido=0,
        status=StatusRescisao.EM_CONFERENCIA,
    )
    _aplicar_dados(rescisao, dados, colaborador.salario)
    return rescisao_repository.adicionar(db, rescisao)


def obter_rescisao(db: Session, rescisao_id: int) -> Rescisao:
    rescisao = rescisao_repository.buscar_por_id(db, rescisao_id)
    if rescisao is None:
        raise LookupError("Rescisão não encontrada")
    return rescisao


def listar_rescisoes(db: Session) -> list[Rescisao]:
    return rescisao_repository.listar(db)


def corrigir_rescisao(db: Session, rescisao_id: int, dados: RescisaoCriar) -> Rescisao:
    """Correção manual dos dados. Se o PDF já existia, volta para EM_CONFERENCIA (precisa gerar de novo)."""
    rescisao = obter_rescisao(db, rescisao_id)
    if rescisao.status not in _STATUS_CORRIGIVEIS:
        raise ValueError("Esta rescisão não pode ser corrigida no status atual")
    _validar_causa(dados.causa_afastamento)

    colaborador = colaborador_repository.buscar_por_id(db, rescisao.colaborador_id)
    if colaborador is None:
        raise LookupError("Colaborador da rescisão não encontrado")
    _aplicar_dados(rescisao, dados, colaborador.salario)
    rescisao.status = StatusRescisao.EM_CONFERENCIA
    rescisao.caminho_pdf = None  # o PDF antigo não vale mais
    return rescisao_repository.salvar(db, rescisao)


def gerar_pdf(db: Session, rescisao_id: int) -> Rescisao:
    """Gera o PDF da rescisão e muda o status para GERADO (ou ERRO_GERACAO)."""
    rescisao = obter_rescisao(db, rescisao_id)
    if rescisao.status not in (StatusRescisao.EM_CONFERENCIA, StatusRescisao.ERRO_GERACAO):
        raise ValueError("O PDF só pode ser gerado para rescisões em conferência")

    colaborador = colaborador_repository.buscar_por_id(db, rescisao.colaborador_id)
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
        rescisao_repository.salvar(db, rescisao)  # grava a falha antes de avisar o erro
        raise RuntimeError(f"Falha ao gerar o PDF: {e}") from e

    rescisao.caminho_pdf = str(destino)
    rescisao.status = StatusRescisao.GERADO
    return rescisao_repository.salvar(db, rescisao)


def caminho_do_pdf(db: Session, rescisao_id: int) -> Path:
    rescisao = obter_rescisao(db, rescisao_id)
    if not rescisao.caminho_pdf or not Path(rescisao.caminho_pdf).exists():
        raise FileNotFoundError("O PDF desta rescisão ainda não foi gerado")
    return Path(rescisao.caminho_pdf)


def enviar_email(db: Session, rescisao_id: int, destinatario: str | None = None) -> Rescisao:
    """Envia o PDF por e-mail. Registra sucesso (ENVIADO) ou falha (ERRO_ENVIO)."""
    rescisao = obter_rescisao(db, rescisao_id)
    if rescisao.status not in _STATUS_ENVIAVEIS:
        raise ValueError("Gere o PDF da rescisão antes de enviar por e-mail")

    colaborador = colaborador_repository.buscar_por_id(db, rescisao.colaborador_id)
    destino = (destinatario or (colaborador.email if colaborador else "") or "").strip()
    if "@" not in destino:
        raise ValueError("Informe um e-mail de destinatário válido")

    pdf = caminho_do_pdf(db, rescisao_id)
    nome = colaborador.nome if colaborador else "colaborador(a)"
    assunto = f"Termo de rescisão de contrato de trabalho — {nome}"
    corpo = (
        f"Olá,\n\nsegue em anexo o termo de rescisão de contrato de trabalho de {nome}.\n\n"
        "Este e-mail foi enviado automaticamente."
    )

    try:
        email_service.enviar_email_com_anexo(destino, assunto, corpo, pdf)
    except Exception as e:
        rescisao.status = StatusRescisao.ERRO_ENVIO
        rescisao_repository.registrar_envio(db, rescisao.id, destino, False, str(e))
        raise RuntimeError(f"Falha ao enviar o e-mail: {e}") from e

    rescisao.status = StatusRescisao.ENVIADO
    rescisao_repository.registrar_envio(db, rescisao.id, destino, True)
    return rescisao


def listar_envios(db: Session, rescisao_id: int):
    obter_rescisao(db, rescisao_id)  # garante que a rescisão existe (404 se não)
    return rescisao_repository.listar_envios(db, rescisao_id)
