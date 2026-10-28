
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from app.core.paths import STATIC_DIR

from app.routers import colaboradores, emails, empresas, historico, rescisoes, ui


app = FastAPI(title="Gerenciamento de Funcionários")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(empresas.router)
app.include_router(colaboradores.router)
app.include_router(historico.router)
app.include_router(emails.router)


@app.get("/", tags=["Sistema"])
def inicio():
    return RedirectResponse(url="/painel")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)
app.include_router(rescisoes.router)
app.include_router(ui.router)
