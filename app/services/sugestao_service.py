"""Sugestão de valores da rescisão (simplificada). Tudo aqui é só SUGESTÃO: a pessoa confere e edita.

Regras usadas (CLT, de forma simples):
- Saldo de salário (30): salário ÷ 30 × dias do mês até o desligamento (no máximo 30).
- 13º proporcional (31): salário ÷ 12 × avos. Conta 1 avo por mês do ano com 15 dias ou mais trabalhados.
- Férias proporcionais (35): salário ÷ 12 × avos, contados desde o último aniversário de admissão
  (mesma regra dos 15 dias). O terço constitucional (36) é 1/3 delas.
- FGTS 8% (42): 8% sobre o saldo de salário e o 13º proporcional (informativo: fora do líquido).
- Justa causa: 13º e férias proporcionais não são devidos, então não são sugeridos.

NÃO são calculados: INSS, IRRF, multa de 40% do FGTS, férias vencidas e aviso prévio.
"""
from calendar import monthrange
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

CENTAVOS = Decimal("0.01")
CAUSA_JUSTA_CAUSA = "Demissão por justa causa"
CODIGOS_SUGERIDOS = (30, 31, 35, 36, 42)  # as verbas que este módulo preenche


def _arredondar(valor: Decimal) -> Decimal:
    return valor.quantize(CENTAVOS, rounding=ROUND_HALF_UP)


def _somar_meses(data: date, meses: int) -> date:
    indice = data.year * 12 + (data.month - 1) + meses
    ano, mes = divmod(indice, 12)
    mes += 1
    return date(ano, mes, min(data.day, monthrange(ano, mes)[1]))


def avos_13(admissao: date, desligamento: date) -> int:
    """Meses do ano do desligamento com 15 dias ou mais trabalhados."""
    ano = desligamento.year
    inicio = admissao if admissao.year == ano else date(ano, 1, 1)
    avos = 0
    for mes in range(inicio.month, desligamento.month + 1):
        primeiro = inicio.day if mes == inicio.month else 1
        ultimo = desligamento.day if mes == desligamento.month else monthrange(ano, mes)[1]
        if ultimo - primeiro + 1 >= 15:
            avos += 1
    return avos


def avos_ferias(admissao: date, desligamento: date) -> int:
    """Meses completos desde o último aniversário de admissão (resto de 15 dias ou mais conta 1)."""

    def aniversario(ano: int) -> date:
        try:
            return admissao.replace(year=ano)
        except ValueError:  # admitido em 29/02
            return date(ano, 2, 28)

    inicio = aniversario(desligamento.year)
    if inicio > desligamento:
        inicio = aniversario(desligamento.year - 1)
    fim = desligamento + timedelta(days=1)  # o dia do desligamento conta
    meses = 0
    while _somar_meses(inicio, meses + 1) <= fim:
        meses += 1
    if (fim - _somar_meses(inicio, meses)).days >= 15:
        meses += 1
    return min(meses, 12)


def formatar_brl(valor: Decimal) -> str:
    texto = f"{valor:,.2f}"  # 2,500.00
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _item(codigo: int, descricao: str, valor: Decimal, referencia: str, explicacao: str) -> dict:
    return {"codigo": codigo, "descricao": descricao, "valor": f"{valor:.2f}", "referencia": referencia or None, "explicacao": explicacao}


def sugerir_verbas(
    salario, data_admissao: date | None, data_desligamento: date, causa: str, origem: str = "salário do cadastro"
) -> dict:
    """Devolve {"itens": [...], "avisos": [...]}. Itens com valor zero não são sugeridos.

    `salario` é a base de cálculo (o salário do cadastro ou a remuneração digitada no formulário);
    `origem` só diz de onde ela veio, para aparecer no aviso.
    """
    avisos: list[str] = []
    salario = Decimal(str(salario)) if salario not in (None, "") else Decimal("0")
    if salario <= 0:
        return {"itens": [], "avisos": ["O colaborador está sem salário no cadastro: não foi possível sugerir valores."]}

    itens: list[dict] = []
    avisos.append(f"Base de cálculo: {formatar_brl(salario)} ({origem}).")
    dias = min(data_desligamento.day, 30)
    saldo = _arredondar(salario / 30 * dias)
    if saldo > 0:
        itens.append(_item(30, "Saldo de Salário", saldo, str(dias), f"salário ÷ 30 × {dias} dias trabalhados no mês"))
    base_fgts = saldo

    if causa == CAUSA_JUSTA_CAUSA:
        avisos.append("Demissão por justa causa: 13º e férias proporcionais não são devidos, por isso não foram sugeridos.")
    elif data_admissao is None:
        avisos.append("O colaborador está sem data de admissão no cadastro: 13º e férias proporcionais não foram sugeridos.")
    elif data_admissao > data_desligamento:
        avisos.append("A data de desligamento é anterior à data de admissão: confira as datas.")
    else:
        a13 = avos_13(data_admissao, data_desligamento)
        v13 = _arredondar(salario / 12 * a13)
        if v13 > 0:
            itens.append(_item(31, "13º Salário", v13, str(a13), f"salário ÷ 12 × {a13}/12 avos"))
            base_fgts += v13
        af = avos_ferias(data_admissao, data_desligamento)
        vf = _arredondar(salario / 12 * af)
        if vf > 0:
            itens.append(_item(35, "Férias proporc.", vf, str(af), f"salário ÷ 12 × {af}/12 avos"))
            itens.append(_item(36, "1/3 sob férias proporc.", _arredondar(vf / 3), "", "1/3 das férias proporcionais"))

    fgts = _arredondar(base_fgts * Decimal("0.08"))
    if fgts > 0:
        itens.append(_item(42, "FGTS 8%", fgts, "", "8% sobre o saldo de salário e o 13º proporcional (informativo)"))

    avisos.append(
        "Valores sugeridos de forma simplificada: confira e ajuste. "
        "Não foram calculados INSS, IRRF, multa de 40% do FGTS, férias vencidas nem aviso prévio."
    )
    return {"itens": itens, "avisos": avisos}
