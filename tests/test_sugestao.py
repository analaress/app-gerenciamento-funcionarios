"""Cálculo das sugestões de verbas (sem banco): contas conferidas à mão."""
from datetime import date
from decimal import Decimal

from app.services.sugestao_service import (
    CAUSA_JUSTA_CAUSA,
    _somar_meses,
    avos_13,
    avos_ferias,
    formatar_brl,
    sugerir_verbas,
)

SEM_JUSTA_CAUSA = "Demissão sem justa causa"


def _por_codigo(resultado):
    return {i["codigo"]: i for i in resultado["itens"]}


def test_sugestao_completa_sem_justa_causa():
    # salário 3.000, admitido em 10/02/2024, desligado em 15/10/2026
    r = sugerir_verbas(Decimal("3000.00"), date(2024, 2, 10), date(2026, 10, 15), SEM_JUSTA_CAUSA)
    itens = _por_codigo(r)
    assert sorted(itens) == [30, 31, 35, 36, 42]
    assert (itens[30]["valor"], itens[30]["referencia"]) == ("1500.00", "15")    # 3000 ÷ 30 × 15
    assert (itens[31]["valor"], itens[31]["referencia"]) == ("2500.00", "10")    # 3000 ÷ 12 × 10 avos (jan a out)
    assert (itens[35]["valor"], itens[35]["referencia"]) == ("2000.00", "8")     # 3000 ÷ 12 × 8 avos (desde 10/02/2026)
    assert itens[36]["valor"] == "666.67"                                        # 1/3 de 2.000,00
    assert itens[42]["valor"] == "320.00"                                        # 8% de (1.500 + 2.500)
    assert all(i["explicacao"] for i in r["itens"]) and r["avisos"]


def test_sugestao_usa_a_base_informada_e_diz_de_onde_ela_veio():
    # a remuneração digitada no formulário (2.500) vale mais que o salário do cadastro
    r = sugerir_verbas(
        Decimal("2500.00"), date(2024, 2, 10), date(2026, 10, 15), SEM_JUSTA_CAUSA, "remuneração informada no formulário"
    )
    itens = _por_codigo(r)
    assert itens[30]["valor"] == "1250.00"                                       # 2500 ÷ 30 × 15
    assert itens[31]["valor"] == "2083.33"                                       # 2500 ÷ 12 × 10
    assert itens[35]["valor"] == "1666.67"                                       # 2500 ÷ 12 × 8
    assert itens[36]["valor"] == "555.56"                                        # 1/3 de 1.666,67
    assert itens[42]["valor"] == "266.67"                                        # 8% de (1.250,00 + 2.083,33)
    assert r["avisos"][0] == "Base de cálculo: R$ 2.500,00 (remuneração informada no formulário)."
    padrao = sugerir_verbas(Decimal("3000.00"), date(2024, 2, 10), date(2026, 10, 15), SEM_JUSTA_CAUSA)
    assert padrao["avisos"][0] == "Base de cálculo: R$ 3.000,00 (salário do cadastro)."
    assert formatar_brl(Decimal("1234567.5")) == "R$ 1.234.567,50" and formatar_brl(Decimal("0")) == "R$ 0,00"


def test_sugestao_para_a_maria_dos_dados_de_teste():
    r = sugerir_verbas(Decimal("3800.00"), date(2023, 6, 23), date(2026, 10, 15), SEM_JUSTA_CAUSA)
    itens = _por_codigo(r)
    assert itens[30]["valor"] == "1900.00"
    assert (itens[31]["valor"], itens[31]["referencia"]) == ("3166.67", "10")
    assert (itens[35]["valor"], itens[35]["referencia"]) == ("1266.67", "4")     # 4 avos desde 23/06/2026
    assert itens[36]["valor"] == "422.22"
    assert itens[42]["valor"] == "405.33"                                        # 8% de (1.900,00 + 3.166,67)


def test_justa_causa_nao_sugere_13_nem_ferias():
    r = sugerir_verbas(Decimal("3000.00"), date(2024, 2, 10), date(2026, 10, 15), CAUSA_JUSTA_CAUSA)
    itens = _por_codigo(r)
    assert sorted(itens) == [30, 42] and itens[42]["valor"] == "120.00"          # 8% só do saldo de salário
    assert any("justa causa" in a for a in r["avisos"])


def test_sem_data_de_admissao_ou_sem_salario_ou_datas_trocadas():
    r = sugerir_verbas(Decimal("3000.00"), None, date(2026, 10, 15), SEM_JUSTA_CAUSA)
    assert sorted(_por_codigo(r)) == [30, 42] and any("admissão" in a for a in r["avisos"])
    r = sugerir_verbas(None, date(2024, 2, 10), date(2026, 10, 15), SEM_JUSTA_CAUSA)
    assert r["itens"] == [] and "salário" in r["avisos"][0]
    r = sugerir_verbas(Decimal("3000.00"), date(2027, 1, 1), date(2026, 10, 15), SEM_JUSTA_CAUSA)
    assert sorted(_por_codigo(r)) == [30, 42] and any("anterior" in a for a in r["avisos"])


def test_saldo_de_salario_no_maximo_30_dias():
    dia_31 = _por_codigo(sugerir_verbas(Decimal("3000.00"), date(2024, 2, 10), date(2026, 10, 31), SEM_JUSTA_CAUSA))
    assert dia_31[30]["valor"] == "3000.00" and dia_31[30]["referencia"] == "30"
    fevereiro = _por_codigo(sugerir_verbas(Decimal("3000.00"), date(2024, 2, 10), date(2026, 2, 28), SEM_JUSTA_CAUSA))
    assert fevereiro[30]["valor"] == "2800.00" and fevereiro[30]["referencia"] == "28"


def test_avos_do_13_so_contam_meses_com_15_dias_ou_mais():
    assert avos_13(date(2020, 1, 1), date(2026, 12, 31)) == 12
    assert avos_13(date(2020, 1, 1), date(2026, 10, 14)) == 9     # outubro tem só 14 dias: não conta
    assert avos_13(date(2020, 1, 1), date(2026, 10, 15)) == 10    # 15 dias: conta
    assert avos_13(date(2026, 3, 20), date(2026, 10, 15)) == 7    # março (12 dias) não conta; abr a out contam
    assert avos_13(date(2026, 10, 1), date(2026, 10, 14)) == 0
    r = sugerir_verbas(Decimal("3000.00"), date(2026, 10, 1), date(2026, 10, 14), SEM_JUSTA_CAUSA)
    assert sorted(_por_codigo(r)) == [30, 42]                     # 13º e férias zerados não aparecem


def test_avos_das_ferias_contam_desde_o_ultimo_aniversario():
    assert avos_ferias(date(2023, 6, 23), date(2026, 10, 15)) == 4          # 3 meses + 23 dias
    assert avos_ferias(date(2025, 11, 20), date(2026, 3, 5)) == 3           # 3 meses + 14 dias
    assert avos_ferias(date(2024, 2, 29), date(2026, 3, 10)) == 0           # admitido em 29/02
    assert avos_ferias(date(2026, 3, 1), date(2026, 10, 15)) == 7 + 1       # 7 meses + 15 dias


def test_somar_meses_respeita_o_fim_do_mes():
    assert _somar_meses(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert _somar_meses(date(2026, 11, 30), 3) == date(2027, 2, 28)
    assert _somar_meses(date(2026, 5, 10), 8) == date(2027, 1, 10)
