from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.repositories import colaborador_repository
from app.routers import colaboradores, rescisoes

app = FastAPI(title="Teste de Rescisões")

# Só é necessário se o front chamar a API direto, sem o proxy do Vite.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(colaboradores.router)
app.include_router(rescisoes.router)


@app.get("/colaboradores-teste", tags=["Teste"])
def listar_colaboradores_teste():
    return colaborador_repository.listar()