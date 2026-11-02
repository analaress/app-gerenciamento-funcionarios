"""Cria empresas e colaboradores de TESTE no banco (dados fictícios, só para desenvolver).

Rode na raiz do projeto, com o .venv ativo e depois do `python -m alembic upgrade head`:

    python scripts/carregar_dados_teste.py

Pode rodar mais de uma vez: quem já existe (mesmo CNPJ / mesmo CPF) é pulado.
"""
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

# permite rodar de qualquer lugar: coloca a raiz do projeto no caminho do Python
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from app.core.database import SessionLocal
from app.models.colaborador import Colaborador
from app.models.empresa import Empresa

EMPRESAS = [
    dict(
        razao_social="Alves e Filhos Ltda", nome_fantasia="Alves e Filhos", cnpj="11.222.333/0001-81",
        email="contato@alves.example.com", telefone="(11) 3333-0001", cep="01310-100",
        logradouro="Av. Principal", numero="500", complemento="Sala 2", bairro="Industrial",
        cidade="São Paulo", estado="SP", representante_legal="Carlos Alves",
    ),
    dict(
        razao_social="Cunha Comércio Ltda", nome_fantasia="Cunha", cnpj="45.723.174/0001-10",
        email="contato@cunha.example.com", telefone="(21) 3333-0002", cep="20040-020",
        logradouro="Rua do Comércio", numero="75", complemento=None, bairro="Centro",
        cidade="Rio de Janeiro", estado="RJ", representante_legal="Marta Cunha",
    ),
]

COLABORADORES = [
    dict(nome="Maria Souza Teste", cpf="11144477735", email="maria.souza@teste.example", cargo="Analista administrativo",
         cnpj="11.222.333/0001-81", salario=Decimal("3800.00"), data_admissao=date(2023, 6, 23),
         pis_pasep="123.45678.90-1", logradouro="Rua das Flores, 100", bairro="Centro", municipio="São Paulo",
         uf="SP", cep="01000-000", ctps="1234567 - 0001 / SP", data_nascimento=date(1990, 10, 30), nome_mae="Ana Souza"),
    dict(nome="João Pereira Teste", cpf="52998224725", email="joao.pereira@teste.example", cargo="Auxiliar de produção",
         cnpj="11.222.333/0001-81", salario=Decimal("2100.00"), data_admissao=date(2021, 2, 1),
         pis_pasep="234.56789.01-2", logradouro="Rua das Palmeiras, 45", bairro="Vila Nova", municipio="São Paulo",
         uf="SP", cep="01100-000", ctps="2345678 - 0002 / SP", data_nascimento=date(1988, 4, 12), nome_mae="Rita Pereira"),
    dict(nome="Rafaela Lima Teste", cpf="39053344705", email="rafaela.lima@teste.example", cargo="Vendedora",
         cnpj="45.723.174/0001-10", salario=Decimal("4850.00"), data_admissao=date(2022, 10, 3),
         pis_pasep="345.67890.12-3", logradouro="Rua do Sol, 300", bairro="Copacabana", municipio="Rio de Janeiro",
         uf="RJ", cep="22000-000", ctps="3456789 - 0003 / RJ", data_nascimento=date(1992, 1, 22), nome_mae="Lúcia Lima"),
    dict(nome="Carlos Andrade Teste", cpf="86288366757", email="carlos.andrade@teste.example", cargo="Motorista",
         cnpj="45.723.174/0001-10", salario=Decimal("2900.00"), data_admissao=date(2019, 8, 15),
         pis_pasep="456.78901.23-4", logradouro="Av. das Nações, 900", bairro="Tijuca", municipio="Rio de Janeiro",
         uf="RJ", cep="20500-000", ctps="4567890 - 0004 / RJ", data_nascimento=date(1985, 7, 9), nome_mae="Sônia Andrade"),
]


def main() -> int:
    try:
        with SessionLocal() as db:
            ids = {}
            novas = 0
            for dados in EMPRESAS:
                empresa = db.scalar(select(Empresa).where(Empresa.cnpj == dados["cnpj"]))
                if empresa is None:
                    empresa = Empresa(**dados)
                    db.add(empresa)
                    db.commit()
                    db.refresh(empresa)
                    novas += 1
                ids[dados["cnpj"]] = empresa.id

            novos = 0
            for dados in COLABORADORES:
                if db.scalar(select(Colaborador).where(Colaborador.cpf == dados["cpf"])) is not None:
                    continue
                campos = {k: v for k, v in dados.items() if k != "cnpj"}
                db.add(Colaborador(empresa_id=ids[dados["cnpj"]], situacao="ATIVO", **campos))
                db.commit()
                novos += 1
    except OperationalError as erro:
        print("Não consegui gravar no banco:", str(erro).splitlines()[0])
        print("Rode antes: python -m alembic upgrade head")
        return 1

    print(f"Empresas novas: {novas} | colaboradores novos: {novos} (quem já existia foi pulado)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
