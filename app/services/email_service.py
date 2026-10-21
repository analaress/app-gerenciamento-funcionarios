import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

from app.repositories import email_repository

load_dotenv()  # lê as configurações do arquivo .env


def _email_valido(endereco: str) -> bool:
    usuario, _, dominio = endereco.partition("@")
    return bool(usuario) and "." in dominio and " " not in endereco


def _montar_mensagem(destinatario, assunto, corpo, pdf, nome_arquivo) -> EmailMessage:
    mensagem = EmailMessage()
    mensagem["From"] = os.getenv("SMTP_FROM") or os.getenv("SMTP_USER") or "nao-responder@exemplo.com"
    mensagem["To"] = destinatario
    mensagem["Subject"] = assunto
    mensagem.set_content(corpo)
    mensagem.add_attachment(pdf, maintype="application", subtype="pdf", filename=nome_arquivo)
    return mensagem


def _enviar_smtp(mensagem: EmailMessage) -> None:
    host = os.getenv("SMTP_HOST")
    porta = int(os.getenv("SMTP_PORT") or 587)
    usuario = os.getenv("SMTP_USER")
    senha = os.getenv("SMTP_PASSWORD")

    if porta == 465:
        servidor = smtplib.SMTP_SSL(host, porta, timeout=15)
    else:
        servidor = smtplib.SMTP(host, porta, timeout=15)

    with servidor:
        servidor.ehlo()
        if porta != 465 and servidor.has_extn("starttls"):
            servidor.starttls()
            servidor.ehlo()
        if usuario and senha:
            servidor.login(usuario, senha)
        servidor.send_message(mensagem)


def enviar_documento(
    documento_id: int,
    destinatario: str,
    pdf: bytes,
    nome_arquivo: str = "documento.pdf",
    assunto: str = "Seu documento",
    corpo: str = "Olá,\n\nSegue em anexo o seu documento.\n",
) -> dict:
    """Envia o PDF por e-mail e registra o resultado (ENVIADO ou ERRO_ENVIO)."""
    erro = None
    simulado = not os.getenv("SMTP_HOST")  # sem servidor configurado: modo de teste

    if not _email_valido(destinatario):
        erro = "E-mail do destinatário inválido."
    elif not simulado:
        try:
            _enviar_smtp(_montar_mensagem(destinatario, assunto, corpo, pdf, nome_arquivo))
        except Exception as e:  # qualquer falha de envio vira ERRO_ENVIO
            erro = f"Falha no envio: {e}"

    status = "ERRO_ENVIO" if erro else "ENVIADO"
    return email_repository.registrar(documento_id, destinatario, status, erro, simulado)
