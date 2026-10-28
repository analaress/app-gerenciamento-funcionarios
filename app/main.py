
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, Response
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
    return HTMLResponse(
        """<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'>
        <meta name='viewport' content='width=device-width,initial-scale=1'>
        <link rel='stylesheet' href='/static/styles.css'><title>Gerenciamento</title></head>
        <body><main class='card'><h1>Gerenciamento de Funcionários</h1>
        <p>API e painel inicial disponíveis.</p><p>
        <a class='button' href='/docs'>Documentação da API</a>
        <a class='button' href='/ui'>Tela inicial</a></p></main></body></html>"""
    )


@app.get("/ui", response_class=HTMLResponse, include_in_schema=False)
def tela_inicial():
    return HTMLResponse(
        """<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'>
        <meta name='viewport' content='width=device-width,initial-scale=1'>
        <link rel='stylesheet' href='/static/styles.css'><title>Painel</title></head>
        <body><main class='card'><h1>Painel de Gerenciamento</h1>
        <p>Escolha uma área:</p><nav class='nav'>
        <a href='/docs'>API</a><a href='/empresas'>Empresas</a>
        <a href='/colaboradores/'>Colaboradores</a><a href='/historico'>Histórico</a>
        <a href='/rescisoes'>Rescisões</a><a href='/emails'>E-mails</a>
        </nav></main></body></html>"""
    )


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)
app.include_router(rescisoes.router)
app.include_router(ui.router)
