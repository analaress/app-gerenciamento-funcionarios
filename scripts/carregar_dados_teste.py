"""Popula o banco com colaboradores de mentira, gerados pelo Faker (nenhum dado digitado à mão).

Rode na raiz do projeto, com o .venv ativo e depois do `alembic upgrade head`:

    python scripts/carregar_dados_teste.py              # cria 10, se o banco estiver vazio
    python scripts/carregar_dados_teste.py --qtd 25     # outra quantidade
    python scripts/carregar_dados_teste.py --adicionar  # soma aos que já existem
"""
import argparse
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

# permite rodar de qualquer lugar: coloca a raiz do projeto no caminho do Python
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from faker import Faker
from sqlalchemy.exc import OperationalError

from app.core.database import SessionLocal
from app.repositories import colaborador_repository, empresa_repository

fake = Faker("pt_BR")


def _so_digitos(texto: str) -> str:
    """'123.456.789-09' -> '12345678909' (a coluna cpf guarda só os 11 números)."""
    return "".join(ch for ch in texto if ch.isdigit())


def _nome() -> str:
    return f"{fake.first_name()} {fake.last_name()} {fake.last_name()}"


def _novo_colaborador(db, ids_empresas: list[int]) -> dict:
    while True:  # o CPF é único no banco
        cpf = _so_digitos(fake.cpf())
        if colaborador_repository.buscar_por_cpf(db, cpf) is None:
            break
    uf = fake.estado_sigla()
    return {
        "nome": _nome()[:150],
        "cpf": cpf,
        "email": fake.email(),
        "cargo": fake.job()[:100],
        "empresa_id": fake.random_element(ids_empresas),
        "salario": Decimal(fake.random_int(1500, 6000, 50)).quantize(Decimal("0.01")),
        "situacao": "ATIVO",
        "data_admissao": fake.date_between(start_date=date(2018, 1, 1), end_date=date(2025, 12, 31)),
        "pis_pasep": fake.numerify("###.#####.##-#"),
        "logradouro": fake.street_address()[:150],
        "bairro": fake.bairro()[:100],
        "municipio": fake.city()[:100],
        "uf": uf,
        "cep": fake.postcode(),
        "ctps": f"{fake.numerify('#######')} - {fake.numerify('####')} / {uf}",
        "data_nascimento": fake.date_of_birth(minimum_age=20, maximum_age=60),
        "nome_mae": _nome()[:150],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Carrega colaboradores de teste no banco.")
    ap.add_argument("--qtd", type=int, default=10, help="quantos criar (padrão: 10)")
    ap.add_argument("--adicionar", action="store_true", help="soma aos que já existem")
    args = ap.parse_args()

    ids_empresas = [e.id for e in empresa_repository.listar()]
    if not ids_empresas:
        print("Nenhuma empresa encontrada no empresa_repository.")
        return 1

    try:
        with SessionLocal() as db:
            existentes = len(colaborador_repository.listar(db))
            if existentes and not args.adicionar:
                print(f"O banco já tem {existentes} colaborador(es). Nada foi alterado.")
                print("Use --adicionar para incluir mais.")
                return 0
            for _ in range(args.qtd):
                c = colaborador_repository.criar(db, _novo_colaborador(db, ids_empresas))
                print(f"{c.id:>3}  {c.nome}  (empresa {c.empresa_id})")
    except OperationalError as e:
        print("Não consegui gravar no banco:", str(e).splitlines()[0])
        print("Se a mensagem fala em 'no such table' ou 'no column', rode antes: alembic upgrade head")
        return 1

    print("Pronto.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
