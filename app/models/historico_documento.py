from datetime import date

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class HistoricoDocumento(Base):
    __tablename__ = "historico_documentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    colaborador_nome: Mapped[str] = mapped_column(String(150))
    colaborador_cpf: Mapped[str] = mapped_column(String(14))
    empresa: Mapped[str] = mapped_column(String(150))
    tipo: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    referencia: Mapped[str | None] = mapped_column(String(50))
    data_geracao: Mapped[date | None] = mapped_column(Date)
    data_envio: Mapped[date | None] = mapped_column(Date)
    usuario_responsavel: Mapped[str] = mapped_column(String(100))
