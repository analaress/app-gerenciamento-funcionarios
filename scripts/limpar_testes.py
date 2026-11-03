"""Zera os dados de TESTE de rescisão do banco local, para repetir os testes do zero.

Rode na raiz do projeto, com o servidor PARADO:

    python scripts/limpar_testes.py

O que faz (só no banco SQLite local):
  - reativa os colaboradores que tinham rescisão (voltam para ATIVO);
  - apaga as rescisões, os envios de e-mail e o histórico de rescisões.
Só mexe em dados de rescisão: empresas e colaboradores não são apagados. Antes de apagar, mostra os
números e pede para você digitar SIM. Os PDFs e os e-mails de teste (arquivos em storage/) ficam.
"""
import os
import sqlite3
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def _url_do_banco() -> str:
    url = os.environ.get("DATABASE_URL", "")
    env = RAIZ / ".env"
    if not url and env.exists():
        for linha in env.read_text(encoding="utf-8").splitlines():
            if linha.strip().startswith("DATABASE_URL="):
                url = linha.split("=", 1)[1].strip().strip('"').strip("'")
                break
    return url or "sqlite:///./colaboradores.db"


def _caminho_sqlite(url: str) -> Path:
    if not url.startswith("sqlite:///"):
        raise SystemExit("Este script só funciona com o banco local SQLite (sqlite:///...). Nada foi alterado.")
    caminho = Path(url.replace("sqlite:///", "", 1))
    return caminho if caminho.is_absolute() else RAIZ / caminho


def _tabelas(cur) -> set[str]:
    return {linha[0] for linha in cur.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def contar(caminho: Path) -> dict:
    """Quantos registros seriam afetados (não altera nada)."""
    con = sqlite3.connect(caminho)
    try:
        cur = con.cursor()
        tabelas = _tabelas(cur)

        def total(sql: str, tabela: str) -> int:
            return cur.execute(sql).fetchone()[0] if tabela in tabelas else 0

        return {
            "rescisoes": total("SELECT COUNT(*) FROM rescisoes", "rescisoes"),
            "envios": total("SELECT COUNT(*) FROM envios_rescisao", "envios_rescisao"),
            "historico": total("SELECT COUNT(*) FROM historico_documentos WHERE tipo = 'RESCISAO'", "historico_documentos"),
            "colaboradores_a_reativar": total(
                "SELECT COUNT(*) FROM colaboradores WHERE situacao = 'DESLIGADO' "
                "AND id IN (SELECT colaborador_id FROM rescisoes)",
                "rescisoes" if "colaboradores" in tabelas else "",
            ),
        }
    finally:
        con.close()


def limpar(caminho: Path) -> dict:
    """Faz a limpeza numa única transação (se algo falhar, nada é apagado)."""
    con = sqlite3.connect(caminho)
    try:
        cur = con.cursor()
        tabelas = _tabelas(cur)
        feito = {"colaboradores_reativados": 0, "envios": 0, "rescisoes": 0, "historico": 0}
        with con:  # confirma tudo no final ou desfaz tudo se der erro
            if {"rescisoes", "colaboradores"} <= tabelas:
                feito["colaboradores_reativados"] = cur.execute(
                    "UPDATE colaboradores SET situacao = 'ATIVO' WHERE situacao = 'DESLIGADO' "
                    "AND id IN (SELECT colaborador_id FROM rescisoes)"
                ).rowcount
            if "envios_rescisao" in tabelas:
                feito["envios"] = cur.execute("DELETE FROM envios_rescisao").rowcount
            if "rescisoes" in tabelas:
                feito["rescisoes"] = cur.execute("DELETE FROM rescisoes").rowcount
            if "historico_documentos" in tabelas:
                feito["historico"] = cur.execute("DELETE FROM historico_documentos WHERE tipo = 'RESCISAO'").rowcount
        return feito
    finally:
        con.close()


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    caminho = _caminho_sqlite(_url_do_banco())
    if not caminho.exists():
        print(f"Banco não encontrado em {caminho}. Rode o script na raiz do projeto. Nada foi alterado.")
        return 1

    antes = contar(caminho)
    print(f"Banco: {caminho}")
    print(f"  Rescisões a apagar:                  {antes['rescisoes']}")
    print(f"  Envios de e-mail a apagar:           {antes['envios']}")
    print(f"  Registros de rescisão no histórico:  {antes['historico']}")
    print(f"  Colaboradores desligados a reativar: {antes['colaboradores_a_reativar']}")
    if not any(antes.values()):
        print("\nNada para limpar.")
        return 0

    if "--sim" not in argv and input("\nDigite SIM para apagar e reativar: ").strip().upper() != "SIM":
        print("Cancelado. Nada foi alterado.")
        return 1

    feito = limpar(caminho)
    print(
        f"\nPronto: {feito['rescisoes']} rescisões, {feito['envios']} envios e {feito['historico']} registros do histórico "
        f"apagados; {feito['colaboradores_reativados']} colaboradores reativados."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
