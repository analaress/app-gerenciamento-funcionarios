from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

# .../app/services/pdf_service.py -> .../app/templates
PASTA_TEMPLATES = Path(__file__).resolve().parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(PASTA_TEMPLATES),
    autoescape=select_autoescape(["html"]),
)


def _brl(valor) -> str:
    """1234.5 -> '1.234,50' (vazio se não houver valor)"""
    if valor is None:
        return ""
    texto = f"{valor:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _data(valor) -> str:
    return valor.strftime("%d/%m/%Y") if valor else ""


_env.filters["brl"] = _brl
_env.filters["data"] = _data


def gerar_pdf_rescisao(contexto: dict, destino: Path) -> Path:
    """Preenche o modelo HTML com os dados e salva o PDF em 'destino'."""
    # Import aqui dentro: se o WeasyPrint não estiver instalado (ou faltar o GTK no
    # Windows), só a geração do PDF falha, e o resto do sistema continua funcionando.
    from weasyprint import HTML

    html = _env.get_template("rescisoes/rescisao.html").render(**contexto)
    destino.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html).write_pdf(destino)
    return destino
