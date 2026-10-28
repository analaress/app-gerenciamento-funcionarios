from html import escape
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError

from app.repositories.colaborador_repository import ColaboradorRepository
from app.repositories.empresa_repository import EmpresaRepository
from app.schemas.colaborador import ColaboradorCreate
from app.schemas.email import EmailCreate
from app.services.colaborador_service import ColaboradorService
from app.services.email_service import EmailService

router = APIRouter(prefix="/ui", tags=["interface"])
empresa_repository = EmpresaRepository()
colaborador_repository = ColaboradorRepository()
colaborador_service = ColaboradorService()
email_service = EmailService()


def pagina(titulo: str, conteudo: str) -> str:
    return f'''<!doctype html><html lang="pt-BR"><head>
    <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="/static/styles.css"><title>{titulo}</title></head><body>
    <header class="topbar"><nav class="nav"><span class="brand">Gestão de Funcionários</span>
    <a href="/ui/colaboradores">Colaboradores</a><a href="/ui/colaboradores/novo">Novo cadastro</a>
    <a href="/ui/emails">E-mails</a><a href="/ui/inbox">Caixa de entrada</a><a href="/ui/emails/novo">Enviar e-mail</a></nav></header>
    <main>{conteudo}</main></body></html>'''


def campo(label: str, nome: str, valor: str = "", tipo: str = "text") -> str:
    return (f'<div class="field"><label for="{nome}">{label}</label>'
            f'<input id="{nome}" name="{nome}" type="{tipo}" value="{escape(str(valor))}" required></div>')


def alerta(erro: str) -> str:
    if not erro:
        return ""
    return f"<div class='alert' role='alert'><strong>Atenção:</strong> {escape(erro)}</div>"


@router.get("/colaboradores", response_class=HTMLResponse)
def colaboradores() -> HTMLResponse:
    empresas = empresa_repository.list()
    linhas = []
    for item in colaborador_repository.list():
        empresa = next((e for e in empresas if e["id"] == item["empresa_id"]), {"nome": "Não encontrada"})
        status = "Ativo" if item.get("ativo", True) else "Inativo"
        linhas.append(f"<tr><td>{escape(item['nome'])}</td><td>{escape(item['email'])}</td>"
                      f"<td>{escape(item['cargo'])}</td><td>{escape(empresa['nome'])}</td>"
                      f"<td>R$ {item['salario']:.2f}</td><td><span class='badge'>{status}</span></td></tr>")
    tabela = "".join(linhas) or "<tr><td class='empty' colspan='6'>Nenhum colaborador cadastrado.</td></tr>"
    conteudo = f'''<section class="card"><div class="heading"><div><h1>Colaboradores</h1>
    <p class="muted">Cadastros persistidos em arquivos JSON.</p></div>
    <a class="button" href="/ui/colaboradores/novo">+ Novo colaborador</a></div>
    <div class="table-wrap"><table class="table"><tr><th>Nome</th><th>E-mail</th><th>Cargo</th>
    <th>Empresa</th><th>Salário</th><th>Status</th></tr>{tabela}</table></div></section>'''
    return HTMLResponse(pagina("Colaboradores", conteudo))


def formulario_colaborador(erro: str = "", valores: dict | None = None) -> HTMLResponse:
    valores = valores or {}
    opcoes = "".join(f"<option value='{e['id']}'>{escape(e['nome'])}</option>" for e in empresa_repository.list())
    conteudo = f'''<section class="card form-card"><h1>Novo colaborador</h1>
    <p class="muted">Preencha os dados para salvar no JSON.</p>{alerta(erro)}
    <form class="form" method="post" action="/ui/colaboradores">
    <div class="field"><label for="empresa_id">Empresa</label><select id="empresa_id" name="empresa_id" required>{opcoes}</select></div>
    {campo('Nome', 'nome', valores.get('nome', ''))}{campo('E-mail', 'email', valores.get('email', ''), 'email')}
    {campo('Cargo', 'cargo', valores.get('cargo', ''))}{campo('Salário', 'salario', valores.get('salario', 'R$ 0,00'))}
    <button class="button" type="submit">Salvar colaborador</button></form></section>'''
    return HTMLResponse(pagina("Novo colaborador", conteudo))


@router.get("/colaboradores/novo", response_class=HTMLResponse)
def novo_colaborador() -> HTMLResponse:
    return formulario_colaborador()


@router.post("/colaboradores")
async def criar_colaborador(request: Request):
    dados = parse_qs((await request.body()).decode("utf-8"))
    form = {chave: valores[0] for chave, valores in dados.items()}
    salario = form["salario"].replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        data = ColaboradorCreate(nome=form["nome"], email=form["email"], cargo=form["cargo"], salario=float(salario))
        colaborador_service.criar(int(form["empresa_id"]), data)
    except (ValidationError, ValueError, HTTPException) as error:
        return formulario_colaborador(str(getattr(error, "detail", error)), form)
    return RedirectResponse("/ui/colaboradores", status_code=303)


def formulario_email(erro: str = "", valores: dict | None = None) -> HTMLResponse:
    valores = valores or {}
    opcoes = "".join(f"<option value='{item['id']}'>{escape(item['nome'])} — {escape(item['email'])}</option>"
                     for item in colaborador_repository.list())
    conteudo = f'''<section class="card form-card"><h1>Enviar documento por e-mail</h1>
    <p class="muted">A mensagem será salva em emails_enviados.json e não será enviada externamente.</p>{alerta(erro)}
    <form class="form" method="post" action="/ui/emails">
    <div class="field"><label for="tipo_documento">Documento XLSX</label>
    <select id="tipo_documento" name="tipo_documento" required>
    <option value="recibo">Recibo de pagamento</option>
    <option value="rescisao">Rescisão por fora</option>
    </select></div>
    <div class="field"><label for="colaborador_id">Colaborador</label><select id="colaborador_id" name="colaborador_id" required>{opcoes}</select></div>
    {campo('Assunto', 'assunto', valores.get('assunto', ''))}
    <div class="field"><label for="mensagem">Mensagem</label><textarea id="mensagem" name="mensagem" rows="6" required>{escape(valores.get('mensagem', ''))}</textarea></div>
    <button class="button" type="submit">Simular envio</button></form></section>'''
    return HTMLResponse(pagina("Enviar e-mail", conteudo))


@router.get("/emails", response_class=HTMLResponse)
def emails() -> HTMLResponse:
    linhas = "".join(f"<tr><td>{escape(str(e['enviado_em']))}</td><td>{escape(e['destinatario'])}</td>"
                     f"<td>{escape(e['assunto'])}</td><td>{escape(e['mensagem'])}</td>"
                     f"<td><span class='badge'>{escape(e['status'])} (mock)</span></td></tr>"
                     for e in email_service.listar())
    tabela = linhas or "<tr><td class='empty' colspan='5'>Nenhum e-mail enviado.</td></tr>"
    conteudo = f'''<section class="card"><div class="heading"><div><h1>E-mails simulados</h1>
    <p class="muted">Mensagens registradas no JSON; nada é enviado externamente.</p></div>
    <div><a class="button" href="/ui/inbox">Caixa de entrada</a> <a class="button" href="/ui/emails/novo">+ Enviar e-mail</a></div></div>
    <div class="table-wrap"><table class="table"><tr><th>Data</th><th>Destinatário</th><th>Assunto</th><th>Mensagem</th><th>Status</th></tr>{tabela}</table></div></section>'''
    return HTMLResponse(pagina("E-mails simulados", conteudo))


@router.get("/emails/novo", response_class=HTMLResponse)
def novo_email() -> HTMLResponse:
    return formulario_email()


@router.post("/emails")
async def enviar_email(request: Request):
    dados = parse_qs((await request.body()).decode("utf-8"))
    form = {chave: valores[0] for chave, valores in dados.items()}
    try:
        email_service.enviar_para_colaborador(int(form["colaborador_id"]), EmailCreate(tipo_documento=form.get("tipo_documento", "recibo"), assunto=form["assunto"], mensagem=form["mensagem"]))
    except (ValidationError, ValueError, HTTPException) as error:
        return formulario_email(str(getattr(error, "detail", error)), form)
    return RedirectResponse("/ui/emails", status_code=303)
