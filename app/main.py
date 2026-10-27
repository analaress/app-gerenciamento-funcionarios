
from fastapi import FastAPI

from app.routers import historico

app = FastAPI(title="Gerenciamento de Funcionários")
app.include_router(historico.router)
from app.routers.colaboradores import router as colaboradores_router


app = FastAPI(title="Gerenciamento de Funcionários")

app.include_router(colaboradores_router)
