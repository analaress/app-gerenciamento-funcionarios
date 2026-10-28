
from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response

from app.routers import colaboradores, emails, empresas, historico, rescisoes


app = FastAPI(title="Gerenciamento de Funcionários")

app.include_router(empresas.router)
app.include_router(colaboradores.router)
app.include_router(historico.router)
app.include_router(emails.router)


@app.get("/", tags=["Sistema"])
def inicio():
    return JSONResponse({"mensagem": "API de Gerenciamento de Funcionários", "documentacao": "/docs"})


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)
app.include_router(rescisoes.router)
