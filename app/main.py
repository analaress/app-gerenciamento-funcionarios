
from fastapi import FastAPI

from app.routers import colaboradores, empresas, historico, rescisoes


app = FastAPI(title="Gerenciamento de Funcionários")

app.include_router(empresas.router)
app.include_router(colaboradores.router)
app.include_router(historico.router)
app.include_router(rescisoes.router)
