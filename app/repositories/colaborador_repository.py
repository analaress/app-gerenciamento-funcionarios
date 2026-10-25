"""Colaboradores de mentira (Faker). Quando o banco entrar, só este arquivo muda."""
from datetime import date
from decimal import Decimal

from faker import Faker

from app.models.colaborador import Colaborador
from app.repositories import empresa_repository

QTD_COLABORADORES = 10

fake = Faker("pt_BR")  # a semente já foi definida no empresa_repository

_IDS_EMPRESAS = [e.id for e in empresa_repository.listar()]


def _nome() -> str:
    return f"{fake.first_name()} {fake.last_name()} {fake.last_name()}"


def _gerar(i: int) -> Colaborador:
    uf = fake.estado_sigla()
    return Colaborador(
        id=i,
        nome=_nome(),
        cpf=fake.cpf(),
        email=fake.email(),
        empresa_id=fake.random_element(_IDS_EMPRESAS),
        cargo=fake.job(),
        salario=Decimal(fake.random_int(min=1500, max=6000, step=50)).quantize(Decimal("0.01")),
        data_admissao=fake.date_between(start_date=date(2018, 1, 1), end_date=date(2025, 12, 31)),
        situacao="ATIVO",
        pis_pasep=fake.numerify("###.#####.##-#"),
        logradouro=fake.street_address(),
        bairro=fake.bairro(),
        municipio=fake.city(),
        uf=uf,
        cep=fake.postcode(),
        ctps=f"{fake.numerify('#######')} - {fake.numerify('####')} / {uf}",
        data_nascimento=fake.date_of_birth(minimum_age=20, maximum_age=60),
        nome_mae=_nome(),
    )


_COLABORADORES: dict[int, Colaborador] = {i: _gerar(i) for i in range(1, QTD_COLABORADORES + 1)}


def listar(nome: str | None = None, empresa_id: int | None = None) -> list[Colaborador]:
    lista = list(_COLABORADORES.values())
    if nome:
        lista = [c for c in lista if nome.lower() in c.nome.lower()]
    if empresa_id:
        lista = [c for c in lista if c.empresa_id == empresa_id]
    return lista


def obter(colaborador_id: int) -> Colaborador | None:
    return _COLABORADORES.get(colaborador_id)
