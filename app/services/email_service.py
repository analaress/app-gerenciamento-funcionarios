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
"""Envio de e-mail (SMTP) com o PDF da rescisão em anexo.

As configurações vêm do arquivo .env (na raiz do projeto):
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
"""
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

try:  # lê o .env automaticamente (pip install python-dotenv)
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # sem a biblioteca, usa só as variáveis do sistema
    pass


class EmailNaoConfiguradoError(RuntimeError):
    """O .env não tem os dados do servidor de e-mail."""


def _configuracao() -> dict:
    host = os.getenv("SMTP_HOST", "").strip()
    usuario = os.getenv("SMTP_USER", "").strip()
    # senhas de app do Gmail são mostradas com espaços; remove para funcionar
    senha = os.getenv("SMTP_PASSWORD", "").replace(" ", "")
    if not host or not usuario or not senha:
        raise EmailNaoConfiguradoError(
            "E-mail não configurado: preencha SMTP_HOST, SMTP_USER e SMTP_PASSWORD no arquivo .env "
            "e reinicie o servidor."
        )
    return {
        "host": host,
        "porta": int(os.getenv("SMTP_PORT", "587") or 587),
        "usuario": usuario,
        "senha": senha,
        "remetente": os.getenv("SMTP_FROM", "").strip() or usuario,
    }


def enviar_email_com_anexo(
    destinatario: str,
    assunto: str,
    corpo: str,
    anexo: Path | None = None,
) -> None:
    """Envia o e-mail. Levanta exceção se der qualquer problema (quem chamou registra a falha)."""
    cfg = _configuracao()

    mensagem = EmailMessage()
    mensagem["From"] = cfg["remetente"]
    mensagem["To"] = destinatario
    mensagem["Subject"] = assunto
    mensagem.set_content(corpo)

    if anexo is not None:
        mensagem.add_attachment(
            Path(anexo).read_bytes(),
            maintype="application",
            subtype="pdf",
            filename=Path(anexo).name,
        )

    if cfg["porta"] == 465:  # conexão já criptografada
        with smtplib.SMTP_SSL(cfg["host"], cfg["porta"], timeout=30) as servidor:
            servidor.login(cfg["usuario"], cfg["senha"])
            servidor.send_message(mensagem)
    else:  # 587: começa simples e passa para criptografado (STARTTLS)
        with smtplib.SMTP(cfg["host"], cfg["porta"], timeout=30) as servidor:
            servidor.starttls()
            servidor.login(cfg["usuario"], cfg["senha"])
            servidor.send_message(mensagem)
