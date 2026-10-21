"""Empresas de mentira (Faker). Quando o banco entrar, só este arquivo muda."""
from faker import Faker

from app.models.empresa import Empresa

QTD_EMPRESAS = 3

Faker.seed(42)  # mesmos dados a cada execução; apague a linha para dados novos sempre
fake = Faker("pt_BR")

_EMPRESAS: dict[int, Empresa] = {
    i: Empresa(
        id=i,
        razao_social=fake.company(),
        cnpj=fake.cnpj(),
        email=fake.company_email(),
        logradouro=fake.street_address(),
        bairro=fake.bairro(),
        municipio=fake.city(),
        uf=fake.estado_sigla(),
        cep=fake.postcode(),
        cnae=fake.numerify("####-#/##"),
    )
    for i in range(1, QTD_EMPRESAS + 1)
}


def listar() -> list[Empresa]:
    return list(_EMPRESAS.values())


def obter(empresa_id: int) -> Empresa | None:
    return _EMPRESAS.get(empresa_id)

