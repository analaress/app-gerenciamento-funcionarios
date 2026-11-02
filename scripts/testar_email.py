"""Testa o envio de e-mail sem abrir o sistema. Nunca mostra a senha.

Rode na raiz do projeto, com o .venv ativo:

    python scripts/testar_email.py                          # só mostra a configuração (não envia nada)
    python scripts/testar_email.py voce@exemplo.com         # envia, respeitando o EMAIL_SIMULADO do .env
    python scripts/testar_email.py voce@exemplo.com --real  # envia DE VERDADE (ignora EMAIL_SIMULADO=true)
"""
import argparse
import os
import smtplib
import socket
import sys
from pathlib import Path

# permite rodar de qualquer lugar: coloca a raiz do projeto no caminho do Python
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services import email_service

NOMES = ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM", "EMAIL_SIMULADO")


def _mascarar(endereco: str) -> str:
    nome, _, dominio = endereco.partition("@")
    return f"{nome[:2]}***@{dominio}" if dominio else "(sem @)"


def mostrar_configuracao() -> list[str]:
    """Mostra o que está preenchido (sem a senha) e devolve os nomes obrigatórios que faltam."""
    print("Configuração de e-mail (a senha nunca é mostrada):")
    faltam = []
    for nome in NOMES:
        valor = email_service._valor(nome)
        if nome == "SMTP_PASSWORD":
            texto = f"preenchida ({len(valor.replace(' ', ''))} caracteres)" if valor else "VAZIA"
        elif nome in ("SMTP_USER", "SMTP_FROM"):
            texto = _mascarar(valor) if valor else "VAZIO"
        else:
            texto = valor or "VAZIO"
        print(f"  {nome:15} {texto}")
        if not valor and nome in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"):
            faltam.append(nome)
    modo = "TESTE (o e-mail só é gravado em arquivo, nada é enviado)" if email_service.modo_simulado() else "REAL (envia pelo servidor SMTP)"
    print(f"  Modo atual: {modo}")
    return faltam


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Testa o envio de e-mail do sistema.")
    ap.add_argument("destino", nargs="?", help="e-mail que vai receber o teste (use o SEU)")
    ap.add_argument("--real", action="store_true", help="envia de verdade, mesmo com EMAIL_SIMULADO=true no .env")
    args = ap.parse_args(argv)

    if args.real:
        os.environ["EMAIL_SIMULADO"] = "false"  # vale só para esta execução; o .env não é alterado

    faltam = mostrar_configuracao()
    if not args.destino:
        print("\nNada foi enviado. Para testar, informe o seu e-mail:")
        print("  python scripts/testar_email.py voce@exemplo.com --real")
        return 1 if (faltam and not email_service.modo_simulado()) else 0

    if "@" not in args.destino:
        print("\nO destinatário precisa ser um e-mail, por exemplo voce@exemplo.com.")
        return 1

    print(f"\nEnviando um e-mail de teste para {_mascarar(args.destino)} ...")
    try:
        email_service.enviar_email_com_anexo(
            args.destino,
            "Teste de e-mail do sistema de rescisões",
            "Olá,\n\nEste é um e-mail de teste do sistema de gerenciamento de funcionários.\n"
            "Se você recebeu esta mensagem, o envio está funcionando.",
            None,
        )
    except email_service.EmailNaoConfiguradoError as erro:
        print("\nNÃO ENVIADO: e-mail não configurado.")
        print(f"  Faltam no .env: {', '.join(faltam) or 'algum dado do servidor de e-mail'}")
        print(f"  ({erro})")
        return 1
    except smtplib.SMTPAuthenticationError:
        print("\nNÃO ENVIADO: o servidor RECUSOU o usuário ou a senha (erro 535).")
        print("  No Gmail, a SMTP_PASSWORD precisa ser uma SENHA DE APP (16 letras), e não a senha normal.")
        print("  Crie uma em https://myaccount.google.com/apppasswords (exige a verificação em duas etapas),")
        print("  cole em SMTP_PASSWORD no .env, salve e rode este teste de novo.")
        return 1
    except smtplib.SMTPRecipientsRefused:
        print("\nNÃO ENVIADO: o servidor recusou o destinatário. Confira se o e-mail está certo.")
        return 1
    except (smtplib.SMTPException, socket.gaierror, TimeoutError, ConnectionError, OSError) as erro:
        print(f"\nNÃO ENVIADO: não foi possível falar com o servidor de e-mail ({type(erro).__name__}: {erro}).")
        print("  Confira SMTP_HOST (Gmail: smtp.gmail.com), SMTP_PORT (587) e a sua conexão com a internet.")
        return 1
    except Exception as erro:  # qualquer outra coisa: mostra o tipo para eu conseguir ajudar
        print(f"\nNÃO ENVIADO: erro inesperado ({type(erro).__name__}: {erro}).")
        return 1

    if email_service.modo_simulado():
        pasta = email_service.PASTA_EMAILS_SIMULADOS
        arquivos = sorted(pasta.glob("*.eml"), key=lambda p: p.stat().st_mtime)
        print("\nMODO DE TESTE: nada foi enviado de verdade. O e-mail foi gravado em arquivo:")
        print(f"  {arquivos[-1] if arquivos else pasta}")
        print("Para enviar de verdade, rode de novo com --real.")
    else:
        print("\nENVIADO. Abra o e-mail de destino e confira a caixa de entrada e o Spam.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
