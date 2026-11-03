import logging
import re
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy.orm import Session

from app.models.rescisao import RUBRICAS, Rescisao, StatusRescisao, TipoItem
from app.repositories import (
    colaborador_repository,
    empresa_repository,
    historico_repository,
    rescisao_repository,
)
from app.schemas.historico import HistoricoCriar, TipoDocumento
from app.schemas.rescisao import MOTIVOS, RescisaoCriar
from app.services import email_service, historico_service, pdf_service, sugestao_service
from app.services.calculo_service import calcular_totais

# .../app/services/rescisao_service.py -> raiz do projeto
RAIZ_PROJETO = Path(__file__).resolve().parents[2]
PASTA_PDFS = RAIZ_PROJETO / "storage" / "documents" / "rescisoes"

# Em quais situações ainda dá para corrigir os dados (a correção volta para EM_CONFERENCIA)
_CORRIGIVEIS = (
    StatusRescisao.EM_CONFERENCIA.value,
    StatusRescisao.GERADO.value,
    StatusRescisao.ENVIADO.value,
    StatusRescisao.ERRO_GERACAO.value,
    StatusRescisao.ERRO_ENVIO.value,
)
# Em quais situações dá para gerar o PDF
_GERAVEIS = (StatusRescisao.EM_CONFERENCIA.value, StatusRescisao.ERRO_GERACAO.value)
# Em quais situações o PDF já existe e pode ser enviado
_ENVIAVEIS = (
    StatusRescisao.GERADO.value,
    StatusRescisao.ENVIADO.value,
    StatusRescisao.ERRO_ENVIO.value,
)


def _colaborador_desligado(colaborador) -> bool:
    return str(getattr(colaborador, "situacao", "") or "").upper() == "DESLIGADO"


# e-mail com formato válido: texto@dominio.xx (sem espaços, com ponto no domínio)
_PADRAO_EMAIL = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}$")


def email_valido(texto: str | None) -> bool:
    return bool(_PADRAO_EMAIL.match((texto or "").strip()))


USUARIO_RESPONSAVEL = "RH Operacional"  # quem aparece como responsável no histórico de documentos

_log = logging.getLogger(__name__)


def _datas_reais(db: Session, registro: Rescisao):
    """Datas VERDADEIRAS: a do arquivo PDF e a do último envio com sucesso.

    Assim o histórico mostra quando o documento foi gerado/enviado de fato, e não o dia em que o
    registro do histórico foi preenchido.
    """
    gerado = None
    if registro.caminho_pdf:
        try:
            gerado = date.fromtimestamp(Path(registro.caminho_pdf).stat().st_mtime)
        except OSError:  # o arquivo foi apagado
            gerado = None
    sucessos = [e.data for e in rescisao_repository.listar_envios(db, registro.id) if e.sucesso]
    enviado = max(sucessos).date() if sucessos else None
    return gerado, enviado


def _sincronizar_historico(db: Session, registro: Rescisao, colaborador=None, empresa=None) -> None:
    """Mantém o histórico de documentos (tabela historico_documentos) em dia com a rescisão.

    Cria o registro se ele não existir e atualiza status e datas quando algo mudou. Também corrige
    registros antigos, porque as datas vêm sempre dos fatos (arquivo do PDF e envios gravados).
    Um problema aqui NUNCA derruba a operação principal: só vai para o log.
    """
    try:
        referencia = f"rescisao-{registro.id}"
        gerado, enviado = _datas_reais(db, registro)
        enviou_ou_tentou = registro.status in (StatusRescisao.ENVIADO.value, StatusRescisao.ERRO_ENVIO.value)
        data_geracao = gerado
        data_envio = enviado if enviou_ou_tentou else None

        existente = next(
            (
                h
                for h in historico_repository.listar(tipo=TipoDocumento.RESCISAO.value)
                if h.get("referencia") == referencia
            ),
            None,
        )
        if existente is None:
            colaborador = colaborador or colaborador_repository.buscar_por_id(db, registro.colaborador_id)
            empresa = empresa or empresa_repository.buscar_empresa(db, registro.empresa_id)
            if colaborador is None or empresa is None:
                return
            historico_service.registrar(
                HistoricoCriar(
                    colaborador_nome=colaborador.nome,
                    colaborador_cpf=colaborador.cpf,
                    empresa=empresa.nome_fantasia or empresa.razao_social,
                    tipo=TipoDocumento.RESCISAO,
                    status=registro.status,
                    referencia=referencia,
                    data_geracao=data_geracao,
                    data_envio=data_envio,
                    usuario_responsavel=USUARIO_RESPONSAVEL,
                )
            )
            return
        novos = {"status": registro.status, "data_geracao": data_geracao, "data_envio": data_envio}
        if any(existente.get(campo) != valor for campo, valor in novos.items()):
            historico_repository.atualizar(existente["id"], **novos)
    except Exception:  # o histórico não pode quebrar a rescisão
        _log.exception("Não foi possível atualizar o histórico da rescisão %s", registro.id)


def _validar_causa(causa: str) -> None:
    if causa not in MOTIVOS:
        raise ValueError("Causa do afastamento inválida")


def _montar_itens(itens_entrada) -> list[dict]:
    """Descrição e tipo vêm da tabela de rubricas do TRCT, não do usuário.

    Os itens ficam guardados na própria rescisão (coluna JSON), ordenados por código e com id 1..n.
    """
    itens = []
    for numero, entrada in enumerate(sorted(itens_entrada, key=lambda i: i.codigo), start=1):
        descricao_padrao, tipo = RUBRICAS[entrada.codigo]
        itens.append({
            "id": numero,
            "codigo": entrada.codigo,
            "descricao": entrada.descricao or descricao_padrao,
            "tipo": tipo.value,
            "valor": str(entrada.valor),
            "referencia": entrada.referencia,
        })
    return itens


def _totais(itens: list[dict]) -> dict[str, Decimal]:
    """Totais 46, 54 e 55 do TRCT: sempre calculados aqui, nunca digitados."""
    para_calculo = [
        SimpleNamespace(tipo=TipoItem(i["tipo"]), valor=Decimal(i["valor"])) for i in itens
    ]
    return calcular_totais(para_calculo)


def _aplicar_dados(registro: Rescisao, dados: RescisaoCriar, colaborador) -> None:
    itens = _montar_itens(dados.itens)
    totais = _totais(itens)

    registro.data_aviso_previo = dados.data_aviso_previo
    registro.data_desligamento = dados.data_desligamento
    registro.causa_afastamento = dados.causa_afastamento
    registro.codigo_afastamento = dados.codigo_afastamento
    registro.pensao_alimenticia = dados.pensao_alimenticia
    registro.categoria_trabalhador = dados.categoria_trabalhador
    # sem remuneração informada, usa o salário cadastrado do colaborador
    registro.remuneracao = (
        dados.remuneracao if dados.remuneracao is not None else (colaborador.salario or Decimal("0"))
    )
    registro.observacoes = dados.observacoes
    registro.itens = itens  # atribuir uma lista nova é o que avisa o banco da mudança
    registro.total_proventos = totais["proventos"]
    registro.total_descontos = totais["descontos"]
    registro.total_liquido = totais["liquido"]


def criar(db: Session, dados: RescisaoCriar) -> Rescisao:
    _validar_causa(dados.causa_afastamento)

    colaborador = colaborador_repository.buscar_por_id(db, dados.colaborador_id)
    if colaborador is None:
        raise LookupError("Colaborador não encontrado")
    if _colaborador_desligado(colaborador):
        raise ValueError("Este colaborador já está desligado: não é possível criar uma nova rescisão para ele")
    existente = rescisao_repository.buscar_por_colaborador(db, colaborador.id)
    if existente is not None:
        raise ValueError(
            f"Este colaborador já tem a rescisão #{existente.id}. Abra-a para corrigir, gerar o PDF ou reenviar."
        )
    empresa = empresa_repository.buscar_empresa(db, colaborador.empresa_id)
    if empresa is None:
        raise LookupError("Empresa do colaborador não encontrada")

    registro = Rescisao(
        colaborador_id=colaborador.id,
        empresa_id=colaborador.empresa_id,  # preenchido automaticamente
        status=StatusRescisao.EM_CONFERENCIA.value,
    )
    _aplicar_dados(registro, dados, colaborador)
    salvo = rescisao_repository.adicionar(db, registro)
    _sincronizar_historico(db, salvo, colaborador, empresa)
    return salvo


def listar(db: Session) -> list[Rescisao]:
    registros = rescisao_repository.listar(db)
    for registro in registros:  # mantém o histórico (no banco) em dia, inclusive o de rescisões antigas
        _sincronizar_historico(db, registro)
    return registros


def obter(db: Session, rescisao_id: int) -> Rescisao:
    registro = rescisao_repository.buscar_por_id(db, rescisao_id)
    if registro is None:
        raise LookupError("Rescisão não encontrada")
    return registro


def corrigir(db: Session, rescisao_id: int, dados: RescisaoCriar) -> Rescisao:
    """Correção manual. Se o PDF já existia, volta para EM_CONFERENCIA (precisa gerar de novo)."""
    registro = obter(db, rescisao_id)
    if registro.status not in _CORRIGIVEIS:
        raise ValueError("Esta rescisão não pode ser corrigida no status atual")
    _validar_causa(dados.causa_afastamento)

    colaborador = colaborador_repository.buscar_por_id(db, registro.colaborador_id)
    if colaborador is None:
        raise LookupError("Colaborador da rescisão não encontrado")

    _aplicar_dados(registro, dados, colaborador)
    registro.status = StatusRescisao.EM_CONFERENCIA.value
    registro.caminho_pdf = None  # o PDF antigo não vale mais
    salvo = rescisao_repository.salvar(db, registro)
    _sincronizar_historico(db, salvo, colaborador)
    return salvo


def _endereco_empresa(empresa) -> str:
    texto = ", ".join(p for p in (empresa.logradouro, empresa.numero) if p)
    if empresa.complemento:
        texto = f"{texto} - {empresa.complemento}" if texto else empresa.complemento
    return texto


def _dados_pdf(registro: Rescisao, colaborador, empresa) -> dict:
    """Monta o dicionário que o gerador de PDF do projeto (pdf_service) espera."""
    verbas = {
        int(i["codigo"]): {"valor": i["valor"], "ref": i.get("referencia") or ""}
        for i in registro.itens
    }
    verbas[46] = {"valor": registro.total_proventos}  # TOTAL BRUTO
    verbas[54] = {"valor": registro.total_descontos}  # TOTAL DAS DEDUÇÕES
    verbas[55] = {"valor": registro.total_liquido}  # LÍQUIDO A RECEBER
    return {
        "empregador_cnpj": empresa.cnpj,
        "empregador_nome": empresa.razao_social,
        "empregador_endereco": _endereco_empresa(empresa),
        "empregador_bairro": empresa.bairro,
        "empregador_municipio": empresa.cidade,
        "empregador_uf": empresa.estado,
        "empregador_cep": empresa.cep,
        "empregador_cnae": "",
        "tomador_cnpj": "",
        "colaborador_pis": colaborador.pis_pasep,
        "colaborador_nome": colaborador.nome,
        "colaborador_endereco": colaborador.logradouro,
        "colaborador_bairro": colaborador.bairro,
        "colaborador_municipio": colaborador.municipio,
        "colaborador_uf": colaborador.uf,
        "colaborador_cep": colaborador.cep,
        "colaborador_ctps": colaborador.ctps,
        "colaborador_cpf": colaborador.cpf,
        "colaborador_nascimento": colaborador.data_nascimento,
        "colaborador_mae": colaborador.nome_mae,
        "remuneracao": registro.remuneracao,
        "data_admissao": colaborador.data_admissao,
        "data_aviso_previo": registro.data_aviso_previo,
        "data_afastamento": registro.data_desligamento,
        "causa_afastamento": registro.causa_afastamento,
        "codigo_afastamento": registro.codigo_afastamento,
        "pensao_alimenticia": registro.pensao_alimenticia,
        "categoria_trabalhador": registro.categoria_trabalhador,
        "local_data_recebimento": "",
        "orgao_homologador": "",
        "verbas": verbas,
    }


def gerar_pdf(db: Session, rescisao_id: int) -> Rescisao:
    """Gera o PDF da rescisão e muda o status para GERADO (ou ERRO_GERACAO)."""
    registro = obter(db, rescisao_id)
    if registro.status not in _GERAVEIS:
        raise ValueError("O PDF só pode ser gerado para rescisões em conferência")

    colaborador = colaborador_repository.buscar_por_id(db, registro.colaborador_id)
    empresa = empresa_repository.buscar_empresa(db, registro.empresa_id)
    if colaborador is None or empresa is None:
        raise LookupError("Colaborador ou empresa da rescisão não encontrados")

    try:
        conteudo = pdf_service.gerar_rescisao_pdf(_dados_pdf(registro, colaborador, empresa))
        caminho = pdf_service.salvar_pdf(f"rescisao_{registro.id}.pdf", conteudo, str(PASTA_PDFS))
    except Exception as erro:
        registro.status = StatusRescisao.ERRO_GERACAO.value
        rescisao_repository.salvar(db, registro)  # grava a falha antes de avisar o erro
        _sincronizar_historico(db, registro, colaborador, empresa)
        raise RuntimeError(f"Falha ao gerar o PDF: {erro}") from erro

    registro.caminho_pdf = str(caminho)
    registro.status = StatusRescisao.GERADO.value
    salvo = rescisao_repository.salvar(db, registro)
    _sincronizar_historico(db, salvo, colaborador, empresa)
    return salvo


def caminho_do_pdf(db: Session, rescisao_id: int) -> Path:
    registro = obter(db, rescisao_id)
    if not registro.caminho_pdf or not Path(registro.caminho_pdf).exists():
        raise FileNotFoundError("O PDF desta rescisão ainda não foi gerado")
    return Path(registro.caminho_pdf)


def enviar_email(db: Session, rescisao_id: int, destinatario: str | None = None) -> Rescisao:
    """Envia o PDF por e-mail. Registra sucesso (ENVIADO) ou falha (ERRO_ENVIO)."""
    registro = obter(db, rescisao_id)
    if registro.status not in _ENVIAVEIS:
        raise ValueError("Gere o PDF da rescisão antes de enviar por e-mail")

    colaborador = colaborador_repository.buscar_por_id(db, registro.colaborador_id)
    destino = (destinatario or (colaborador.email if colaborador else "") or "").strip()
    if not email_valido(destino):
        raise ValueError("Informe um e-mail de destinatário válido (exemplo: nome@empresa.com.br)")

    pdf = caminho_do_pdf(db, rescisao_id)
    nome = colaborador.nome if colaborador else "colaborador(a)"
    assunto = f"Termo de rescisão de contrato de trabalho — {nome}"
    corpo = (
        f"Olá,\n\nsegue em anexo o termo de rescisão de contrato de trabalho de {nome}.\n\n"
        "Este e-mail foi enviado automaticamente."
    )

    try:
        email_service.enviar_email_com_anexo(destino, assunto, corpo, pdf)
    except Exception as erro:
        registro.status = StatusRescisao.ERRO_ENVIO.value
        rescisao_repository.registrar_envio(db, registro.id, destino, False, str(erro))
        _sincronizar_historico(db, registro, colaborador)
        raise RuntimeError(f"Falha ao enviar o e-mail: {erro}") from erro

    registro.status = StatusRescisao.ENVIADO.value
    rescisao_repository.registrar_envio(db, registro.id, destino, True)
    # e-mail enviado com sucesso = rescisão concluída: o colaborador passa a DESLIGADO e não pode ter outra
    # rescisão. Corrigir, gerar de novo, baixar e reenviar ESTA rescisão continuam permitidos.
    if colaborador is not None and not _colaborador_desligado(colaborador):
        rescisao_repository.marcar_colaborador_desligado(db, colaborador)
    _sincronizar_historico(db, registro, colaborador)
    return registro


def sugerir(db: Session, dados) -> dict:
    """Sugere valores (editáveis) para a tela, a partir do salário, da admissão e da data de desligamento."""
    _validar_causa(dados.causa_afastamento)
    colaborador = colaborador_repository.buscar_por_id(db, dados.colaborador_id)
    if colaborador is None:
        raise LookupError("Colaborador não encontrado")
    remuneracao = getattr(dados, "remuneracao", None)
    if remuneracao:  # a remuneração digitada no formulário vale mais que o salário do cadastro
        base, origem = remuneracao, "remuneração informada no formulário"
    else:
        base, origem = colaborador.salario, "salário do cadastro"
    return sugestao_service.sugerir_verbas(
        base, colaborador.data_admissao, dados.data_desligamento, dados.causa_afastamento, origem
    )


def email_em_modo_de_teste() -> bool:
    """A tela usa isto para avisar que o e-mail NÃO é enviado de verdade (EMAIL_SIMULADO=true)."""
    return email_service.modo_simulado()


def listar_envios(db: Session, rescisao_id: int):
    obter(db, rescisao_id)  # garante que a rescisão existe (404 se não)
    return rescisao_repository.listar_envios(db, rescisao_id)
