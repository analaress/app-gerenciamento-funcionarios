
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.models.colaborador import Colaborador
from app.routers.colaboradores import router


def test_funcionalidades_colaboradores(tmp_path):
    caminho_banco = tmp_path / "teste.db"

    engine = create_engine(
        f"sqlite:///{caminho_banco.as_posix()}",
        connect_args={"check_same_thread": False}
    )

    SessionTeste = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    app = FastAPI()
    app.include_router(router)

    def get_db_teste():
        with SessionTeste() as db:
            yield db

    app.dependency_overrides[get_db] = get_db_teste

    dados = {
        "nome": "Maria Teste",
        "cpf": "12345678901",
        "email": "maria@exemplo.com",
        "cargo": "Desenvolvedora",
        "empresa_id": 1
    }

    try:
        with TestClient(app) as client:

            # Teste 1: Cadastrar colaborador
            resposta = client.post(
                "/colaboradores/", json=dados
            )
            assert resposta.status_code == 201

            colaborador_id = resposta.json()["id"]

            # Teste 2: Listar colaboradores
            resposta = client.get("/colaboradores/")
            assert resposta.status_code == 200
            assert len(resposta.json()) == 1

            # Teste 3: Selecionar colaborador
            resposta = client.get(
                f"/colaboradores/{colaborador_id}"
            )
            assert resposta.status_code == 200
            assert resposta.json()["nome"] == "Maria Teste"

            # Teste 4: Impedir CPF duplicado
            resposta = client.post(
                "/colaboradores/", json=dados
            )
            assert resposta.status_code == 409

            # Teste 5: Colaborador inexistente
            resposta = client.get("/colaboradores/9999")
            assert resposta.status_code == 404

            # Teste 6: CPF com formato inválido
            dados_invalidos = {**dados, "cpf": "123"}
            resposta = client.post(
                "/colaboradores/", json=dados_invalidos
            )
            assert resposta.status_code == 422

    finally:
        engine.dispose()
