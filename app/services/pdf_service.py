from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

PASTA_PADRAO = "storage/documents"
MAX_ITENS = 14  # linhas da tabela de vencimentos/descontos
LINHA = 0.36 * cm
LARGURA_PRINCIPAL = 16.0 * cm
LARGURA_LATERAL = 1.8 * cm
ALTURA_VIA = (2.4 + 0.3 + 1.3 + 0.3 + 0.65 + 1.9 + 1.1) * cm + MAX_ITENS * LINHA
CINZA = colors.HexColor("#C8C8C8")
OBRIGATORIOS = [
    "empregador_nome", "competencia", "colaborador_nome",
    "itens", "total_vencimentos", "total_descontos", "liquido",
]


def _num(valor) -> str:
    """Formata 1234.5 como '1.234,50'. Textos (ex.: faixa do IRRF) passam como estão."""
    if valor is None or valor == "":
        return ""
    try:
        texto = f"{Decimal(str(valor)):,.2f}"
    except InvalidOperation:
        return str(valor)
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _texto(c, x, y, texto, tam=8, negrito=False, alinhar="e", largura=None):
    """Escreve um texto. alinhar: 'e' esquerda, 'd' direita, 'c' centro."""
    fonte = "Helvetica-Bold" if negrito else "Helvetica"
    texto = str(texto)
    if largura:  # diminui a letra até caber
        while tam > 5 and stringWidth(texto, fonte, tam) > largura:
            tam -= 0.5
    c.setFont(fonte, tam)
    if alinhar == "d":
        c.drawRightString(x, y, texto)
    elif alinhar == "c":
        c.drawCentredString(x, y, texto)
    else:
        c.drawString(x, y, texto)


def _via(c, x0, topo, d):
    larg = LARGURA_PRINCIPAL
    y = topo

    # Empregador + título
    h = 2.4 * cm
    c.rect(x0, y - h, larg, h)
    _texto(c, x0 + 0.2 * cm, y - 0.45 * cm, "EMPREGADOR", 7)
    campos = [
        ("Nome", d["empregador_nome"], 13.0),
        ("Endereço", d.get("empregador_endereco", ""), 11.0),
        ("CNPJ", d.get("empregador_cnpj", ""), 8.0),
    ]
    for i, (rotulo, valor, larg_cm) in enumerate(campos):
        yy = y - (1.0 + i * 0.5) * cm
        _texto(c, x0 + 1.6 * cm, yy, rotulo, 7, alinhar="d")
        _texto(c, x0 + 1.8 * cm, yy, valor, 8, largura=larg_cm * cm)
    _texto(c, x0 + larg - 0.2 * cm, y - 0.55 * cm, "Recibo de Pagamento e Salário", 13, True, "d")
    _texto(c, x0 + larg - 0.2 * cm, y - 1.6 * cm, d["competencia"], 11, True, "d")

    # Funcionário
    y -= h + 0.3 * cm
    h = 1.3 * cm
    c.rect(x0, y - h, larg, h)
    cols = [1.8, 7.0, 2.2, 5.0]
    titulos = ["CÓDIGO", "NOME DO FUNCIONÁRIO", "CBO", "FUNÇÃO"]
    valores = [d.get("codigo", ""), d["colaborador_nome"], d.get("cbo", ""), d.get("funcao", "")]
    xs = x0
    for i, w in enumerate(cols):
        if i:
            c.line(xs, y, xs, y - h)
        _texto(c, xs + 0.15 * cm, y - 0.4 * cm, titulos[i], 6.5)
        _texto(c, xs + 0.15 * cm, y - 1.0 * cm, valores[i], 9.5, largura=(w - 0.3) * cm)
        xs += w * cm

    # Tabela de itens
    y -= h + 0.3 * cm
    cols = [1.5, 7.7, 2.3, 2.25, 2.25]
    xcol = [x0]
    for w in cols:
        xcol.append(xcol[-1] + w * cm)
    cab, corpo = 0.65 * cm, MAX_ITENS * LINHA
    c.rect(x0, y - cab - corpo, larg, cab + corpo)
    c.line(x0, y - cab, x0 + larg, y - cab)
    for i, t in enumerate(["Cód.", "Descrição", "Referência", "Vencimentos", "Descontos"]):
        _texto(c, (xcol[i] + xcol[i + 1]) / 2, y - 0.43 * cm, t, 9, True, "c")
        if i:
            c.line(xcol[i], y, xcol[i], y - cab - corpo)
    for n, item in enumerate(d["itens"]):
        yy = y - cab - (n + 1) * LINHA + 0.1 * cm
        _texto(c, xcol[0] + 0.15 * cm, yy, item.get("codigo", ""), 8)
        _texto(c, xcol[1] + 0.15 * cm, yy, item.get("descricao", ""), 8, largura=cols[1] * cm - 0.3 * cm)
        _texto(c, xcol[3] - 0.15 * cm, yy, item.get("referencia", ""), 8, alinhar="d")
        _texto(c, xcol[4] - 0.15 * cm, yy, _num(item.get("vencimento")), 8, alinhar="d")
        _texto(c, xcol[5] - 0.15 * cm, yy, _num(item.get("desconto")), 8, alinhar="d")

    # Mensagens, totais e líquido
    y -= cab + corpo
    h = 1.9 * cm
    c.setFillColor(CINZA)
    c.rect(xcol[4], y - h, xcol[5] - xcol[4], h / 2, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.rect(x0, y - h, larg, h)
    c.line(xcol[3], y, xcol[3], y - h)
    c.line(xcol[4], y, xcol[4], y - h)
    c.line(xcol[3], y - h / 2, x0 + larg, y - h / 2)
    _texto(c, x0 + 0.15 * cm, y - 0.4 * cm, "MENSAGENS", 7)
    for i, linha in enumerate(str(d.get("mensagens", "")).splitlines()[:3]):
        _texto(c, x0 + 0.15 * cm, y - (0.85 + i * 0.35) * cm, linha, 8, largura=xcol[3] - x0 - 0.3 * cm)
    _texto(c, xcol[4] - 0.15 * cm, y - 0.35 * cm, "Total dos Vencimentos", 6.5, alinhar="d", largura=cols[3] * cm - 0.3 * cm)
    _texto(c, xcol[4] - 0.15 * cm, y - 0.8 * cm, _num(d["total_vencimentos"]), 9, alinhar="d")
    _texto(c, xcol[5] - 0.15 * cm, y - 0.35 * cm, "Total dos Descontos", 6.5, alinhar="d", largura=cols[4] * cm - 0.3 * cm)
    _texto(c, xcol[5] - 0.15 * cm, y - 0.8 * cm, _num(d["total_descontos"]), 9, alinhar="d")
    _texto(c, xcol[4] - 0.15 * cm, y - 1.5 * cm, "Líquido a Receber->", 7.5, True, "d", largura=cols[3] * cm - 0.3 * cm)
    _texto(c, xcol[5] - 0.15 * cm, y - 1.55 * cm, _num(d["liquido"]), 11, True, "d")

    # Bases de cálculo
    y -= h
    h = 1.1 * cm
    c.rect(x0, y - h, larg, h)
    itens = [
        ("Salário Base", "salario_base", 2.3), ("Base Cálc. INSS", "base_inss", 2.4),
        ("Base Cálc. FGTS", "base_fgts", 2.4), ("FGTS do Mês", "fgts_mes", 2.6),
        ("Base Cálc. IRRF", "base_irrf", 3.1), ("Faixa IRRF", "faixa_irrf", 3.2),
    ]
    xs = x0
    for rotulo, chave, w in itens:
        meio = xs + w * cm / 2
        _texto(c, meio, y - 0.4 * cm, rotulo, 6.5, alinhar="c")
        _texto(c, meio, y - 0.9 * cm, _num(d.get(chave)), 9, alinhar="c")
        xs += w * cm


def _vertical(c, x, y, texto, tam=7.5):
    """Escreve um texto de baixo para cima (x = linha de base, y = início)."""
    c.saveState()
    c.translate(x, y)
    c.rotate(90)
    c.setFont("Helvetica", tam)
    c.drawString(0, 0, texto)
    c.restoreState()


def _lateral(c, x, topo):
    alt = ALTURA_VIA
    c.rect(x, topo - alt, LARGURA_LATERAL, alt)
    c.line(x + 0.6 * cm, topo, x + 0.6 * cm, topo - alt)
    _vertical(c, x + 0.45 * cm, topo - alt + 0.4 * cm,
              "DECLARO TER RECEBIDO A IMPORTÂNCIA LÍQUIDA DISCRIMINADA NESTE RECIBO.")
    divisoria = topo - 8.6 * cm
    c.line(x + 0.6 * cm, divisoria, x + LARGURA_LATERAL, divisoria)
    _vertical(c, x + 1.25 * cm, divisoria + 2.2 * cm, "ASSINATURA DO FUNCIONÁRIO", 7)
    _vertical(c, x + 1.25 * cm, topo - alt + 2.6 * cm, "DATA", 7)
    _vertical(c, x + 1.25 * cm, topo - alt + 0.4 * cm, "   /       /   ", 9)


def gerar_recibo_pdf(dados: dict) -> bytes:
    """Desenha o recibo (2 vias na mesma página) e devolve o PDF em memória.

    Este serviço só desenha: totais e líquido já chegam calculados.
    """
    faltando = [k for k in OBRIGATORIOS if k not in dados]
    if faltando:
        raise ValueError(f"Faltam dados para o recibo: {', '.join(faltando)}")
    if len(dados["itens"]) > MAX_ITENS:
        raise ValueError(f"O recibo comporta no máximo {MAX_ITENS} itens.")

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setTitle("Recibo de Pagamento e Salário")
    c.setLineWidth(0.6)
    largura, altura = A4
    x0 = 1.5 * cm
    topo1 = altura - 1.2 * cm
    topo2 = topo1 - ALTURA_VIA - 0.8 * cm

    for topo in (topo1, topo2):
        _via(c, x0, topo, dados)
        _lateral(c, x0 + LARGURA_PRINCIPAL + 0.2 * cm, topo)

    c.setDash(3, 3)  # linha de corte entre as duas vias
    corte = topo1 - ALTURA_VIA - 0.4 * cm
    c.line(1.0 * cm, corte, largura - 1.0 * cm, corte)

    c.showPage()
    c.save()
    return buffer.getvalue()


def salvar_pdf(nome_arquivo: str, conteudo: bytes, pasta: str = PASTA_PADRAO) -> Path:
    """Grava o PDF numa pasta e devolve o caminho do arquivo."""
    destino = Path(pasta)
    destino.mkdir(parents=True, exist_ok=True)
    caminho = destino / Path(nome_arquivo).name  # .name impede caminhos perigosos
    caminho.write_bytes(conteudo)
    return caminho


# ---------------------------------------------------------------------------
# Termo de Rescisão do Contrato de Trabalho
# ---------------------------------------------------------------------------

LARGURA_RESCISAO = 19.0 * cm
OBRIGATORIOS_RESCISAO = [
    "empregador_nome", "colaborador_nome", "colaborador_cpf",
    "data_admissao", "data_afastamento", "causa_afastamento", "verbas",
]
CAMPOS_NUMERICOS = {"remuneracao"}

# número do campo -> (nome na tela, unidade mostrada abaixo do nome)
_VERBAS = {
    29: ("Aviso Prévio Indenizado", "dias"), 30: ("Saldo Salário", "dias"),
    31: ("13º Salário", "/12 avos"), 32: ("13º Salário Inden.", "/12 avos"),
    33: ("Férias Vencidas", "/12 avos"), 34: ("1/3 sobre férias vencidas", ""),
    35: ("Férias proporc.", "/12 avos"), 36: ("1/3 sob férias proporc.", ""),
    37: ("Férias Indenizada", "/12 avos"), 38: ("1/3 sob férias indenizada", ""),
    39: ("Reflexo extras DSR", ""), 40: ("Horas extras", "/horas"),
    41: ("Horas Faltas Parcial", "/horas"), 42: ("FGTS 8%", "meses"),
    43: ("FGTS Multa Rescis.", "40%"), 44: ("FGTS Mês rescisão/mês anterior", ""),
    45: ("Faltas", ""), 46: ("TOTAL BRUTO", ""),
    47: ("Previdência", ""), 48: ("Previdência 13º salário", ""),
    49: ("Adiantamentos", ""), 50: ("IRRF", ""), 51: ("Aviso Prévio", ""),
    52: ("Faltas", "dias"), 53: ("Outros descontos", ""),
    54: ("TOTAL DAS DEDUÇÕES", ""), 55: ("LÍQUIDO A RECEBER", ""),
}
_TOTAIS = (46, 54, 55)

# Cada linha: (altura em cm, [(largura em cm, rótulo, chave dos dados), ...])
_EMPREGADOR = [
    (1.0, [(4.8, "01-CNPJ", "empregador_cnpj"), (14.2, "02-NOME", "empregador_nome")]),
    (1.0, [(15.0, "03-Endereço (logradouro, nº, andar, apartamento)", "empregador_endereco"),
           (4.0, "04-Bairro", "empregador_bairro")]),
    (1.0, [(8.0, "05-Município", "empregador_municipio"), (1.6, "06-UF", "empregador_uf"),
           (3.2, "07-CEP", "empregador_cep"), (2.6, "08-CNAE", "empregador_cnae"),
           (3.6, "09-CNPJ/CEI Tomador/O.", "tomador_cnpj")]),
]
_TRABALHADOR = [
    (1.0, [(4.8, "10-PIS-PASEP", "colaborador_pis"), (14.2, "11-Nome", "colaborador_nome")]),
    (1.0, [(15.0, "12-Endereço (logradouro, nº, andar, apartamento)", "colaborador_endereco"),
           (4.0, "13-Bairro", "colaborador_bairro")]),
    (1.0, [(8.0, "14-Município", "colaborador_municipio"), (1.6, "15-UF", "colaborador_uf"),
           (3.2, "16-CEP", "colaborador_cep"),
           (6.2, "17-Carteira de Trabalho (nº, série, UF)", "colaborador_ctps")]),
    (1.0, [(4.0, "18-CPF", "colaborador_cpf"), (4.0, "19-Data Nascimento", "colaborador_nascimento"),
           (11.0, "20-Nome da Mãe", "colaborador_mae")]),
]
_CONTRATO = [
    (1.0, [(6.2, "21-Remuneração p/ fins rescisórios", "remuneracao"),
           (4.2, "22-Data de Admissão", "data_admissao"),
           (4.3, "23-Data do Aviso Prévio", "data_aviso_previo"),
           (4.3, "24-Data do Afastamento", "data_afastamento")]),
    (1.0, [(6.2, "25-Causa do Afastamento", "causa_afastamento"),
           (4.2, "26-Código de Afastam.", "codigo_afastamento"),
           (4.3, "27-Pensão Aliment. %", "pensao_alimenticia"),
           (4.3, "28-Cat. do Trabalhador", "categoria_trabalhador")]),
]
_ASSINATURAS = [
    (1.2, [(9.5, "56-Local e data do Recebimento", "local_data_recebimento"),
           (9.5, "57-Carimbo e assin. do Empregador/preposto", None)]),
    (1.2, [(9.5, "58-Assinatura do Trabalhador", None),
           (9.5, "59-Assinatura do responsável legal do trabalhador", None)]),
]
_TEXTO_HOMOLOGACAO = (
    "Foi prestada, gratuitamente, assistência ao trabalhador, nos termos do art. 477, "
    "§ 1º, da Consolidação das Leis do Trabalho-CLT, sendo comprovado, neste ato, o "
    "efetivo pagamento das verbas rescisórias acima especificadas."
)


def _fmt(valor) -> str:
    """Datas viram dd/mm/aaaa; vazio vira ''; o resto vira texto."""
    if valor is None:
        return ""
    if isinstance(valor, (date, datetime)):
        return valor.strftime("%d/%m/%Y")
    return str(valor)


def _campo(c, x, topo, w, h, rotulo, valor="", tam=8.5):
    c.rect(x, topo - h, w, h)
    _texto(c, x + 0.12 * cm, topo - 0.3 * cm, rotulo, 6.5, largura=w - 0.24 * cm)
    if valor:
        _texto(c, x + 0.12 * cm, topo - h + 0.2 * cm, valor, tam, largura=w - 0.24 * cm)


def _linhas(c, x0, topo, linhas, dados):
    """Desenha as linhas de campos e devolve a nova posição vertical."""
    for altura, campos in linhas:
        x = x0
        for largura, rotulo, chave in campos:
            if chave in CAMPOS_NUMERICOS:
                valor = _num(dados.get(chave))
            else:
                valor = _fmt(dados.get(chave)) if chave else ""
            _campo(c, x, topo, largura * cm, altura * cm, rotulo, valor)
            x += largura * cm
        topo -= altura * cm
    return topo


def _verba(dados, numero):
    verbas = dados.get("verbas", {})
    item = verbas.get(numero, verbas.get(str(numero)))
    if isinstance(item, dict):
        return item.get("valor"), item.get("ref", "")
    return item, ""


def _bloco_verbas(c, x0, topo, dados):
    colunas = [(29, 5.0, 1.7), (38, 4.9, 1.7), (47, 4.0, 1.7)]  # 1º campo, largura do nome, do valor
    cab, linha = 0.6 * cm, 0.78 * cm
    alt = cab + 9 * linha
    c.rect(x0, topo - alt, LARGURA_RESCISAO, alt)
    c.line(x0, topo - cab, x0 + LARGURA_RESCISAO, topo - cab)
    x = x0
    for i, (primeiro, wl, wv) in enumerate(colunas):
        wl, wv = wl * cm, wv * cm
        if i:
            c.line(x, topo, x, topo - alt)
        c.line(x + wl, topo - cab, x + wl, topo - alt)
        if i < 2:
            _texto(c, x + wl + wv / 2, topo - 0.4 * cm, "Valor", 7.5, alinhar="c")
        else:
            _texto(c, x + (wl + wv) / 2, topo - 0.4 * cm, "DEDUÇÕES", 8, True, "c")
        for k in range(9):
            numero = primeiro + k
            nome, unidade = _VERBAS[numero]
            ytopo = topo - cab - k * linha
            if k:
                c.line(x, ytopo, x + wl + wv, ytopo)
            negrito = numero in _TOTAIS[1:]
            _texto(c, x + 0.12 * cm, ytopo - 0.3 * cm, f"{numero}-{nome}", 7, negrito, largura=wl - 0.24 * cm)
            valor, ref = _verba(dados, numero)
            dica = f"{ref} {unidade}".strip() if ref not in (None, "") else unidade
            if dica:
                _texto(c, x + 0.12 * cm, ytopo - 0.62 * cm, dica, 6.5, largura=wl - 0.24 * cm)
            _texto(c, x + wl + wv - 0.12 * cm, ytopo - 0.5 * cm, _num(valor), 8.5, negrito, "d")
        x += wl + wv
    return topo - alt


def _homologacao(c, x0, topo, dados):
    w, h = 9.5 * cm, 4.6 * cm
    c.rect(x0, topo - h, w, h)
    _texto(c, x0 + 0.12 * cm, topo - 0.3 * cm, "60-HOMOLOGAÇÃO", 6.5)
    for i, linha in enumerate(simpleSplit(_TEXTO_HOMOLOGACAO, "Helvetica", 7, w - 0.24 * cm)):
        _texto(c, x0 + 0.12 * cm, topo - (0.7 + i * 0.32) * cm, linha, 7)
    for y, legenda in ((2.55, "Local e Data"), (3.3, "Carimbo e assinatura do assistente")):
        c.line(x0 + 0.12 * cm, topo - y * cm, x0 + 6.5 * cm, topo - y * cm)
        _texto(c, x0 + 0.12 * cm, topo - (y + 0.3) * cm, legenda, 7)
    c.line(x0, topo - 3.75 * cm, x0 + w, topo - 3.75 * cm)
    _texto(c, x0 + 0.12 * cm, topo - 4.05 * cm, "63-Identificação do órgão homologador", 6.5)
    _texto(c, x0 + 0.12 * cm, topo - h + 0.2 * cm, _fmt(dados.get("orgao_homologador")), 8.5, largura=w - 0.24 * cm)

    x = x0 + w
    _campo(c, x, topo, 4.75 * cm, 3.4 * cm, "61-Digital do trabalhador")
    _campo(c, x + 4.75 * cm, topo, 4.75 * cm, 3.4 * cm, "62-Digital do resp. legal")
    _campo(c, x, topo - 3.4 * cm, w, 1.2 * cm, "64-Recepção pelo Banco (data e carimbo)")


def gerar_rescisao_pdf(dados: dict) -> bytes:
    """Desenha o Termo de Rescisão (1 página) e devolve o PDF em memória.

    Este serviço só desenha: as verbas e os totais (campos 46, 54 e 55) já chegam calculados.
    """
    faltando = [k for k in OBRIGATORIOS_RESCISAO if k not in dados]
    if faltando:
        raise ValueError(f"Faltam dados para a rescisão: {', '.join(faltando)}")
    for numero in _TOTAIS:
        if _verba(dados, numero)[0] is None:
            raise ValueError(f"Falta o valor do campo {numero} (os totais já devem chegar calculados).")

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setTitle("Termo de Rescisão do Contrato de Trabalho")
    c.setLineWidth(0.6)
    x0 = 1.0 * cm
    y = A4[1] - 1.5 * cm

    c.rect(x0, y - 0.9 * cm, LARGURA_RESCISAO, 0.9 * cm)
    _texto(c, x0 + LARGURA_RESCISAO / 2, y - 0.6 * cm, "TERMO DE RESCISÃO DO CONTRATO DE TRABALHO", 11, True, "c")
    y -= 1.15 * cm

    for secao in (_EMPREGADOR, _TRABALHADOR, _CONTRATO):
        y = _linhas(c, x0, y, secao, dados) - 0.25 * cm
    y = _bloco_verbas(c, x0, y, dados) - 0.25 * cm
    y = _linhas(c, x0, y, _ASSINATURAS, dados) - 0.25 * cm
    _homologacao(c, x0, y, dados)

    c.showPage()
    c.save()
    return buffer.getvalue()