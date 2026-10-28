from datetime import datetime, timezone
import mimetypes
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from fastapi import HTTPException
from app.repositories.colaborador_repository import ColaboradorRepository
from app.repositories.email_repository import EmailRepository
from app.services.document_service import DocumentService


class EmailService:
    def __init__(self, repository=None, colaboradores=None):
        self.repository = repository or EmailRepository()
        self.colaboradores = colaboradores or ColaboradorRepository()
        self.documentos = DocumentService()

    def enviar_para_colaborador(self, colaborador_id, data):
        colaborador = self.colaboradores.get_by_id(colaborador_id)
        if not colaborador: raise HTTPException(404, "Colaborador não encontrado")
        anexo = self.documentos.gerar_anexo(colaborador, data.tipo_documento)
        registro = {
            "colaborador_id": colaborador_id,
            "destinatario": colaborador["email"],
            "assunto": data.assunto,
            "mensagem": data.mensagem,
            "status": "enviado",
            "enviado_em": datetime.now(timezone.utc).isoformat(),
            "simulado": True,
            "anexo": anexo,
        }
        if os.getenv("EMAIL_PROVIDER", "mock").lower() in ("smtp", "local"):
            self._enviar_smtp(registro, data)
            registro["simulado"] = False
        return self.repository.create(registro)

    def listar(self): return self.repository.list()

    def _enviar_smtp(self, registro, data):
        message = EmailMessage()
        message["From"] = os.getenv("EMAIL_FROM", "sistema@localhost")
        message["To"] = registro["destinatario"]
        message["Subject"] = data.assunto
        message.set_content(data.mensagem)
        anexo = registro.get("anexo")
        if anexo and Path(anexo["caminho"]).exists():
            payload = Path(anexo["caminho"]).read_bytes()
            maintype, subtype = mimetypes.guess_type(anexo["nome"])[0].split("/", 1)
            message.add_attachment(payload, maintype=maintype, subtype=subtype, filename=anexo["nome"])
        provider = os.getenv("EMAIL_PROVIDER", "mock").lower()
        if provider == "local":
            from app.local_mail.server import local_smtp_server
            local_smtp_server.save_message(message.as_bytes())
            return
        host = os.getenv("SMTP_HOST", "127.0.0.1")
        port = int(os.getenv("SMTP_PORT", "2525"))
        with smtplib.SMTP(host, port) as smtp:
            smtp.send_message(message)
