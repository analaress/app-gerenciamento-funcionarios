
from fastapi import FastAPI

from app.routers.colaboradores import router as colaboradores_router
from app.routers.rescisoes import router as rescisoes_router


app = FastAPI(title="Gerenciamento de Funcionários")

app.include_router(colaboradores_router)
app.include_router(rescisoes_router)
