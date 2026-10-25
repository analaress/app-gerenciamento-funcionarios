from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


class StatusRescisao(str, Enum):
    PENDENTE = "PENDENTE"
    EM_CONFERENCIA = "EM_CONFERENCIA"
    GERADO = "GERADO"
    ENVIADO = "ENVIADO"
    ERRO_GERACAO = "ERRO_GERACAO"
    ERRO_ENVIO = "ERRO_ENVIO"


class TipoItem(str, Enum):
    PROVENTO = "PROVENTO"          # soma no TOTAL BRUTO (46)
    DESCONTO = "DESCONTO"          # soma no TOTAL DAS DEDUÇÕES (54)
    INFORMATIVO = "INFORMATIVO"    # aparece no documento, mas não entra no líquido


P, D, I = TipoItem.PROVENTO, TipoItem.DESCONTO, TipoItem.INFORMATIVO

# Rubricas do TRCT (modelo da mentora): código -> (descrição, tipo).
# Os totais 46, 54 e 55 são calculados e não aparecem aqui.
RUBRICAS: dict[int, tuple[str, TipoItem]] = {
    29: ("Aviso Prévio Indenizado", P),
    30: ("Saldo de Salário", P),
    31: ("13º Salário", P),
    32: ("13º Salário Inden.", P),
    33: ("Férias Vencidas", P),
    34: ("1/3 sobre férias vencidas", P),
    35: ("Férias proporc.", P),
    36: ("1/3 sob férias proporc.", P),
    37: ("Outras verbas rescisórias", P),
    38: ("1/3 sob férias indenizada", P),
    39: ("Reflexo extras DSR", P),
    40: ("Horas extras", P),
    41: ("Horas faltas parcial", I),            
    42: ("FGTS 8%", I),
    43: ("FGTS multa rescis.", I),
    44: ("FGTS mês rescisão/mês anterior", I),
    45: ("Faltas", I),                           
    47: ("Previdência", D),
    48: ("Previdência 13º salário", D),
    49: ("Adiantamentos", D),
    50: ("IRRF", D),
    51: ("Aviso Prévio", D),
    52: ("Faltas", D),
    53: ("Outros descontos", D),
}


@dataclass
class ItemRescisao:
    id: int
    codigo: int
    descricao: str
    tipo: TipoItem
    valor: Decimal
    referencia: str | None = None   # ex.: "2/12 avos", "30 dias"


@dataclass
class Rescisao:
    id: int
    colaborador_id: int
    empresa_id: int
    data_desligamento: date          # campo 24 (data do afastamento)
    causa_afastamento: str           # campo 25
    remuneracao: Decimal             # campo 21
    itens: list[ItemRescisao]
    total_proventos: Decimal         # campo 46 (TOTAL BRUTO)
    total_descontos: Decimal         # campo 54 (TOTAL DAS DEDUÇÕES)
    total_liquido: Decimal           # campo 55 (LÍQUIDO A RECEBER)
    data_aviso_previo: date | None = None      # campo 23
    codigo_afastamento: str | None = None      # campo 26
    pensao_alimenticia: Decimal | None = None  # campo 27 (%)
    categoria_trabalhador: str = "01 - Empregado"  # campo 28
    observacoes: str | None = None
    status: StatusRescisao = StatusRescisao.EM_CONFERENCIA
    caminho_pdf: str | None = None
    criado_em: datetime = field(default_factory=datetime.now)
