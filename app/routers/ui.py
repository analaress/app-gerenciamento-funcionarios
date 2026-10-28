from types import SimpleNamespace

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.colaborador import Colaborador
from app.models.empresa import Empresa
from app.repositories import email_repository

router = APIRouter(prefix="/painel", tags=["Interface HTML"])
templates = Jinja2Templates(directory="templates")


def _empresa_view(empresa: Empresa) -> SimpleNamespace:
    return SimpleNamespace(id=empresa.id, nome=empresa.nome_fantasia or empresa.razao_social)


@router.get("/colaboradores")
def colaboradores(request: Request):
    with SessionLocal() as db:
        colaboradores_db = db.scalars(select(Colaborador).order_by(Colaborador.id)).all()
        empresas_db = db.scalars(select(Empresa).order_by(Empresa.id)).all()
        colaboradores_view = [SimpleNamespace(
            nome=c.nome, email=c.email, cargo=c.cargo, empresa_id=c.empresa_id,
            salario=float(getattr(c, "salario", 0) or 0), ativo=True,
        ) for c in colaboradores_db]
        return templates.TemplateResponse(
            request=request, name="colaboradores.html",
            context={"colaboradores": colaboradores_view, "empresas": [_empresa_view(e) for e in empresas_db]},
        )


@router.get("")
def painel(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html", context={})


@router.get("/emails")
def emails(request: Request):
    return templates.TemplateResponse(
        request=request, name="emails.html",
        context={"emails": [SimpleNamespace(**item) for item in email_repository.listar_todos()]},
    )
