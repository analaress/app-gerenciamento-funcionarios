
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Colaborador(Base):
    __tablename__ = "colaboradores"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    nome: Mapped[str] = mapped_column(
        String(150), nullable=False
    )

    cpf: Mapped[str] = mapped_column(
        String(11), unique=True, nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(150), nullable=False
    )

    cargo: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    empresa_id: Mapped[int] = mapped_column(
        Integer, nullable=False
    )