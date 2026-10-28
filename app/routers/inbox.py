from email import policy
from email.parser import BytesParser
from html import escape
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from app.core.paths import GENERATED_DIR, INBOX_DIR

router = APIRouter(prefix="/ui/inbox", tags=["inbox local"])
INBOX = INBOX_DIR


@router.get("", response_class=HTMLResponse)
def inbox():
    messages = []
    for path in sorted(INBOX.glob("*.eml"), key=lambda item: item.stat().st_mtime, reverse=True):
        message = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
        messages.append({
            "id": path.stem,
            "subject": message.get("subject", "(sem assunto)"),
            "sender": message.get("from", ""),
            "recipient": message.get("to", ""),
            "body": message.get_body(preferencelist=("plain", "html")).get_content() if message.get_body() else "",
            "attachments": [part.get_filename() for part in message.iter_attachments() if part.get_filename()],
        })
    def links_anexos(item):
        return "".join(
            f"<a class='button' href='/ui/inbox/anexo/{item['id']}_{escape(name)}'>"
            f"Baixar {escape(name)}</a> <a class='button' href='/ui/inbox/preview/{Path(name).stem}.pdf'>Visualizar PDF</a> "
            for name in item["attachments"]
        ) or "nenhum"

    cards = "".join(
        f"<article class='mail-card'><h2>{escape(item['subject'])}</h2>"
        f"<p><strong>De:</strong> {escape(item['sender'])}<br><strong>Para:</strong> {escape(item['recipient'])}</p>"
        f"<pre>{escape(item['body'])}</pre>"
        f"<p><strong>Anexos:</strong> {links_anexos(item)}</p></article>"
        for item in messages
    ) or "<p class='empty'>Nenhum e-mail recebido ainda.</p>"
    html = f"<html lang='pt-BR'><head><meta charset='utf-8'><link rel='stylesheet' href='/static/styles.css'><title>Caixa local</title></head><body><header class='topbar'><nav class='nav'><span class='brand'>Caixa de e-mail local</span><a href='/ui/emails/novo'>Enviar teste</a><a href='/ui/colaboradores'>Colaboradores</a></nav></header><main><section class='card'><h1>Caixa de entrada local</h1><p class='muted'>Servidor SMTP local. Nenhuma mensagem sai do computador.</p>{cards}</section></main></body></html>"
    return HTMLResponse(html)


@router.get("/anexo/{filename}")
def baixar_anexo(filename: str):
    path = (INBOX / Path(filename).name).resolve()
    if not path.exists() or path.parent != INBOX.resolve():
        return HTMLResponse("Anexo não encontrado", status_code=404)
    return FileResponse(path)


@router.get("/preview/{filename}")
def preview_pdf(filename: str):
    path = (GENERATED_DIR / Path(filename).name).resolve()
    if not path.exists() and path.suffix.lower() == ".pdf":
        prefix = path.stem.rsplit("_", 1)[0]
        alternativas = sorted(
            path.parent.glob(f"{prefix}_*.pdf"),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
        if alternativas:
            return RedirectResponse(f"/ui/inbox/preview/{alternativas[0].name}")
    if path.suffix.lower() != ".pdf" or not path.exists() or path.parent != GENERATED_DIR.resolve():
        return HTMLResponse("Preview não encontrado", status_code=404)
    return FileResponse(path, media_type="application/pdf")
