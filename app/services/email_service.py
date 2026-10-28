import os
import smtplib
from datetime import date

from email.message import EmailMessage

from dotenv import load_dotenv

from app.repositories import email_repository

from app.services import historico_service

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
    registro = email_repository.registrar(documento_id, destinatario, status, erro, simulado)
    historico_service.atualizar_status(
        documento_id, status, date.today() if status == "ENVIADO" else None
    )
    return registro
"""Envio de e-mail (SMTP) com o PDF da rescisão em anexo.

As configurações vêm do arquivo .env (na raiz do projeto):
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
"""
import os
import smtplib
import re
from datetime import datetime
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


# .../app/services/email_service.py -> raiz do projeto
PASTA_EMAILS_SIMULADOS = (
    Path(__file__).resolve().parents[2] / "storage" / "documents" / "temporary" / "emails_simulados"
)


def _simulado() -> bool:
    """EMAIL_SIMULADO=true no .env: o e-mail é gravado num arquivo .eml, em vez de enviado."""
    return os.getenv("EMAIL_SIMULADO", "").strip().lower() in ("1", "true", "sim", "yes")


def _gravar_eml_simulado(destinatario: str, assunto: str, corpo: str, anexo: Path | None) -> Path:
    """Monta o e-mail completo (com o PDF anexo) e salva como .eml. Nada sai do computador."""
    mensagem = EmailMessage()
    mensagem["From"] = os.getenv("SMTP_FROM", "").strip() or "simulado@localhost"
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
    PASTA_EMAILS_SIMULADOS.mkdir(parents=True, exist_ok=True)
    seguro = re.sub(r"[^A-Za-z0-9@._-]", "_", destinatario)
    caminho = PASTA_EMAILS_SIMULADOS / f"{datetime.now():%Y%m%d_%H%M%S_%f}_{seguro}.eml"
    caminho.write_bytes(mensagem.as_bytes())
    return caminho


def enviar_email_com_anexo(
    destinatario: str,
    assunto: str,
    corpo: str,
    anexo: Path | None = None,
) -> None:
    """Envia o e-mail. Levanta exceção se der qualquer problema (quem chamou registra a falha)."""
    if _simulado():  # modo de teste: grava o .eml e não envia nada
        _gravar_eml_simulado(destinatario, assunto, corpo, anexo)
        return

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
