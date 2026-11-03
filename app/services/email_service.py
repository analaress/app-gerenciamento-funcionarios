"""Envio de e-mail com anexo (SMTP) e modo de teste.

Modo de teste: com EMAIL_SIMULADO=true no .env, o e-mail NÃO é enviado: ele é gravado como
arquivo .eml em storage/documents/temporary/emails_simulados (dá para abrir e conferir o PDF anexo).
"""
import os
import re
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

# .../app/services/email_service.py -> raiz do projeto
RAIZ_PROJETO = Path(__file__).resolve().parents[2]
PASTA_EMAILS_SIMULADOS = RAIZ_PROJETO / "storage" / "documents" / "temporary" / "emails_simulados"


class EmailNaoConfiguradoError(RuntimeError):
    """O .env não tem os dados do servidor de e-mail."""


def _arquivo_env() -> dict[str, str]:
    """Lê o .env da raiz do projeto (CHAVE=valor). Não precisa de biblioteca extra."""
    valores: dict[str, str] = {}
    try:
        texto = (RAIZ_PROJETO / ".env").read_text(encoding="utf-8-sig")
    except OSError:
        return valores
    for linha in texto.splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.partition("=")
        valores[chave.strip()] = valor.strip().strip('"').strip("'")
    return valores


def _valor(nome: str, padrao: str = "") -> str:
    """Variável de ambiente primeiro; se não existir, o que estiver no .env."""
    return os.environ.get(nome) or _arquivo_env().get(nome) or padrao


def _simulado() -> bool:
    """EMAIL_SIMULADO=true: grava um .eml em vez de enviar."""
    return _valor("EMAIL_SIMULADO").strip().lower() in ("1", "true", "sim", "yes")


def modo_simulado() -> bool:
    """True quando EMAIL_SIMULADO está ligado: o e-mail só é gravado em arquivo, nada é enviado."""
    return _simulado()


def _configuracao() -> dict:
    host = _valor("SMTP_HOST").strip()
    usuario = _valor("SMTP_USER").strip()
    # senhas de app do Gmail são mostradas com espaços; remove para funcionar
    senha = _valor("SMTP_PASSWORD").replace(" ", "")
    if not host or not usuario or not senha:
        raise EmailNaoConfiguradoError(
            "E-mail não configurado: preencha SMTP_HOST, SMTP_USER e SMTP_PASSWORD no arquivo .env "
            "e reinicie o servidor."
        )
    return {
        "host": host,
        "porta": int(_valor("SMTP_PORT", "587") or 587),
        "usuario": usuario,
        "senha": senha,
        "remetente": _valor("SMTP_FROM").strip() or usuario,
    }


def _montar_mensagem(
    remetente: str, destinatario: str, assunto: str, corpo: str, anexo: Path | None
) -> EmailMessage:
    mensagem = EmailMessage()
    mensagem["From"] = remetente
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
    return mensagem


def _gravar_eml_simulado(destinatario: str, assunto: str, corpo: str, anexo: Path | None) -> Path:
    """Monta o e-mail completo (com o PDF anexo) e salva como .eml. Nada sai do computador."""
    mensagem = _montar_mensagem(
        _valor("SMTP_FROM").strip() or "simulado@localhost", destinatario, assunto, corpo, anexo
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
    mensagem = _montar_mensagem(cfg["remetente"], destinatario, assunto, corpo, anexo)

    if cfg["porta"] == 465:  # conexão já criptografada
        with smtplib.SMTP_SSL(cfg["host"], cfg["porta"], timeout=30) as servidor:
            servidor.login(cfg["usuario"], cfg["senha"])
            servidor.send_message(mensagem)
    else:  # 587: começa simples e passa para criptografado (STARTTLS)
        with smtplib.SMTP(cfg["host"], cfg["porta"], timeout=30) as servidor:
            servidor.starttls()
            servidor.login(cfg["usuario"], cfg["senha"])
            servidor.send_message(mensagem)
