from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

def gerar_preview_recibo(nome: str, email: str, cargo: str, salario: float, destino: Path) -> Path:

    destino.parent.mkdir(parents=True, exist_ok=True)
    documento = SimpleDocTemplate(str(destino), pagesize=A4, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42)
    estilos = getSampleStyleSheet()
    conteudo = [Paragraph("Recibo de Pagamento e Salário", estilos["Title"]), Spacer(1, 20)]
    dados = [
        ["Campo", "Valor"],
        ["Nome", nome],
        ["E-mail", email],
        ["Cargo", cargo],
        ["Salário", f"R$ {salario:,.2f}"],
    ]
    tabela = Table(dados, colWidths=[130, 350])
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172554")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ("PADDING", (0, 0), (-1, -1), 10),
    ]))
    conteudo.append(tabela)
    documento.build(conteudo)
    return destino
