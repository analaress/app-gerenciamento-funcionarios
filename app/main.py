from fastapi import FastAPI

from app.routers import historico

app = FastAPI(title="Gerenciamento de Funcionários")
app.include_router(historico.router)