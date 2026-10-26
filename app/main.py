
from fastapi import FastAPI

from app.routers.colaboradores import router as colaboradores_router


app = FastAPI(title="Gerenciamento de Funcionários")

app.include_router(colaboradores_router)