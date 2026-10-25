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
