"""Modelos da rescisão (tabelas do banco).

Tabelas: rescisoes, itens_rescisao, envios_rescisao.
Os enums (StatusRescisao, TipoItem) e a tabela de rubricas (RUBRICAS) continuam aqui,
com os mesmos nomes de antes: schemas e calculo_service importam daqui.
"""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import Boolean, Date, DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.colaborador import Colaborador  # noqa: F401  (a tabela 'colaboradores' precisa estar carregada para a chave estrangeira)


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


class Rescisao(Base):
    __tablename__ = "rescisoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    colaborador_id: Mapped[int] = mapped_column(
        ForeignKey("colaboradores.id"), nullable=False, index=True
    )
    # Sem chave estrangeira: a tabela 'empresas' ainda não existe (a empresa vem do empresa_repository).
    empresa_id: Mapped[int] = mapped_column(Integer, nullable=False)

    data_aviso_previo: Mapped[date | None] = mapped_column(Date, nullable=True)  # campo 23
    data_desligamento: Mapped[date] = mapped_column(Date, nullable=False)  # campo 24
    causa_afastamento: Mapped[str] = mapped_column(String(120), nullable=False)  # campo 25
    codigo_afastamento: Mapped[str | None] = mapped_column(String(10), nullable=True)  # campo 26
    pensao_alimenticia: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)  # campo 27 (%)
    categoria_trabalhador: Mapped[str] = mapped_column(
        String(60), nullable=False, default="01 - Empregado"
    )  # campo 28
    remuneracao: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)  # campo 21
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Totais: sempre calculados pelo servidor (calculo_service), nunca digitados.
    total_proventos: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)  # campo 46
    total_descontos: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)  # campo 54
    total_liquido: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)  # campo 55

    status: Mapped[StatusRescisao] = mapped_column(
        SAEnum(StatusRescisao, native_enum=False, length=20),
        nullable=False,
        default=StatusRescisao.EM_CONFERENCIA,
    )
    caminho_pdf: Mapped[str | None] = mapped_column(String(255), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

    itens: Mapped[list["ItemRescisao"]] = relationship(
        back_populates="rescisao",
        cascade="all, delete-orphan",
        order_by="ItemRescisao.codigo",
        lazy="selectin",
    )
    envios: Mapped[list["EnvioRescisao"]] = relationship(
        back_populates="rescisao",
        cascade="all, delete-orphan",
        order_by="EnvioRescisao.id",
    )


class ItemRescisao(Base):
    __tablename__ = "itens_rescisao"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rescisao_id: Mapped[int] = mapped_column(
        ForeignKey("rescisoes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Cada código só aparece uma vez por rescisão. Isso é garantido pelo schema (RescisaoCriar),
    # e não por uma restrição UNIQUE no banco, para não atrapalhar a troca dos itens na correção.
    codigo: Mapped[int] = mapped_column(Integer, nullable=False)
    descricao: Mapped[str] = mapped_column(String(120), nullable=False)
    tipo: Mapped[TipoItem] = mapped_column(
        SAEnum(TipoItem, native_enum=False, length=12), nullable=False
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    referencia: Mapped[str | None] = mapped_column(String(40), nullable=True)  # ex.: "2/12 avos"

    rescisao: Mapped["Rescisao"] = relationship(back_populates="itens")


class EnvioRescisao(Base):
    """Cada tentativa de envio do PDF por e-mail (sucesso ou falha)."""

    __tablename__ = "envios_rescisao"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rescisao_id: Mapped[int] = mapped_column(
        ForeignKey("rescisoes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    destinatario: Mapped[str] = mapped_column(String(150), nullable=False)
    data: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    sucesso: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    erro: Mapped[str | None] = mapped_column(Text, nullable=True)

    rescisao: Mapped["Rescisao"] = relationship(back_populates="envios")
