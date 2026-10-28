
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import Date, DateTime, ForeignKey, Integer, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class StatusRescisao(str, Enum):
    PENDENTE = "PENDENTE"
    EM_CONFERENCIA = "EM_CONFERENCIA"
    GERADO = "GERADO"
    ENVIADO = "ENVIADO"
    ERRO_GERACAO = "ERRO_GERACAO"
    ERRO_ENVIO = "ERRO_ENVIO"


class TipoItem(str, Enum):
    PROVENTO = "PROVENTO"
    DESCONTO = "DESCONTO"
    INFORMATIVO = "INFORMATIVO"


P, D, I = TipoItem.PROVENTO, TipoItem.DESCONTO, TipoItem.INFORMATIVO

RUBRICAS: dict[int, tuple[str, TipoItem]] = {
    29: ("Aviso Prévio Indenizado", P), 30: ("Saldo de Salário", P),
    31: ("13º Salário", P), 32: ("13º Salário Inden.", P),
    33: ("Férias Vencidas", P), 34: ("1/3 sobre férias vencidas", P),
    35: ("Férias proporc.", P), 36: ("1/3 sob férias proporc.", P),
    37: ("Outras verbas rescisórias", P), 38: ("1/3 sob férias indenizada", P),
    39: ("Reflexo extras DSR", P), 40: ("Horas extras", P),
    41: ("Horas faltas parcial", I), 42: ("FGTS 8%", I),
    43: ("FGTS multa rescis.", I), 44: ("FGTS mês rescisão/mês anterior", I),
    45: ("Faltas", I), 47: ("Previdência", D), 48: ("Previdência 13º salário", D),
    49: ("Adiantamentos", D), 50: ("IRRF", D), 51: ("Aviso Prévio", D),
    52: ("Faltas", D), 53: ("Outros descontos", D),
}


class Rescisao(Base):
    __tablename__ = "rescisoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    colaborador_id: Mapped[int] = mapped_column(ForeignKey("colaboradores.id"), nullable=False)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False)
    data_aviso_previo: Mapped[date | None] = mapped_column(Date)
    data_desligamento: Mapped[date] = mapped_column(Date, nullable=False)
    causa_afastamento: Mapped[str] = mapped_column(String(150), nullable=False)
    codigo_afastamento: Mapped[str | None] = mapped_column(String(10))
    pensao_alimenticia: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    categoria_trabalhador: Mapped[str] = mapped_column(String(100), nullable=False)
    remuneracao: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    observacoes: Mapped[str | None] = mapped_column(String(1000))
    total_proventos: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_descontos: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_liquido: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    caminho_pdf: Mapped[str | None] = mapped_column(String(500))
    itens: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
