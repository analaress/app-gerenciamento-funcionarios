import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.core.paths import STATIC_DIR
from app.routers import empresas, colaboradores, emails, pages
from app.routers import inbox


def carregar_env():
    arquivo = Path(".env")
    if not arquivo.exists():
        return
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            chave, valor = linha.split("=", 1)
            os.environ.setdefault(chave.strip(), valor.strip().strip('"'))


carregar_env()
from app.local_mail.server import local_smtp_server

@asynccontextmanager
async def lifespan(app):
    if os.getenv("EMAIL_PROVIDER", "mock").lower() == "local":
        await local_smtp_server.start()
    yield
    if os.getenv("EMAIL_PROVIDER", "mock").lower() == "local":
        await local_smtp_server.stop()


app = FastAPI(title="Gerenciamento de Funcionários", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(empresas.router)
app.include_router(colaboradores.router)
app.include_router(emails.router)
app.include_router(pages.router)
app.include_router(inbox.router)
