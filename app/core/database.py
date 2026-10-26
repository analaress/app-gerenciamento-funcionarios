
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfiguracaoBanco(BaseSettings):
    DATABASE_URL: str = "sqlite:///./colaboradores.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore"
    )


config = ConfiguracaoBanco()

# Configuração específica para SQLite
configuracao_conexao = {}

if config.DATABASE_URL.startswith("sqlite"):
    configuracao_conexao = {
        "check_same_thread": False
    }

engine = create_engine(
    config.DATABASE_URL,
    connect_args=configuracao_conexao
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


def get_db():
    with SessionLocal() as db:
        yield db
