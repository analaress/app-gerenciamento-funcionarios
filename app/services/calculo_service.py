from decimal import Decimal, ROUND_HALF_UP

from app.models.rescisao import TipoItem

CENTAVOS = Decimal("0.01")


def _arredondar(valor: Decimal) -> Decimal:
    return valor.quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def calcular_totais(itens) -> dict[str, Decimal]:
    """Recebe itens com .tipo e .valor.

    - PROVENTO soma no total bruto (campo 46 do TRCT)
    - DESCONTO soma no total das deduções (campo 54)
    - INFORMATIVO (FGTS etc.) não entra na conta
    - líquido (campo 55) = bruto - deduções
    """
    proventos = sum((i.valor for i in itens if i.tipo == TipoItem.PROVENTO), Decimal("0"))
    descontos = sum((i.valor for i in itens if i.tipo == TipoItem.DESCONTO), Decimal("0"))
    return {
        "proventos": _arredondar(proventos),
        "descontos": _arredondar(descontos),
        "liquido": _arredondar(proventos - descontos),
    }
