from fastapi import FastAPI

from app.core.database import Base, engine
from app.models import historico_documento  # noqa: F401  (registra a tabela)
from app.routers import historico

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gerenciamento de Funcionários")
app.include_router(historico.router)