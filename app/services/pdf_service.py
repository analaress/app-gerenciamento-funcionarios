from decimal import Decimal, InvalidOperation
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
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