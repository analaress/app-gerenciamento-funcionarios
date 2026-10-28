
from fastapi import FastAPI
from fastapi.responses import RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from app.core.paths import STATIC_DIR

from app.routers import colaboradores, emails, empresas, historico, rescisoes, ui


app = FastAPI(title="Gerenciamento de Funcionários")
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
