from datetime import date

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class HistoricoDocumento(Base):
    """Histórico dos documentos gerados/enviados (recibos e rescisões)."""

    __tablename__ = "historico_documentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    colaborador_nome: Mapped[str] = mapped_column(String(150), nullable=False)
    colaborador_cpf: Mapped[str] = mapped_column(String(20), nullable=False)
    empresa: Mapped[str] = mapped_column(String(150), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)  # RECIBO ou RESCISAO
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    # liga o registro ao documento de origem, ex.: "rescisao-3"
    referencia: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    data_geracao: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_envio: Mapped[date | None] = mapped_column(Date, nullable=True)
    usuario_responsavel: Mapped[str] = mapped_column(String(150), nullable=False)
