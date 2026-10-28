"""Teste da rescisão com banco (SQLite temporário: o colaboradores.db NÃO é tocado)."""
from decimal import Decimal

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.models import rescisao as _modelos_rescisao  # noqa: F401  (registra as tabelas de rescisão)
from app.models.colaborador import Colaborador
from app.routers.rescisoes import router


def _dados(colaborador_id, itens=None, causa="Demissão sem justa causa"):
    return {
        "colaborador_id": colaborador_id,
        "data_desligamento": "2026-10-15",
        "causa_afastamento": causa,
        "itens": itens
        or [
            {"codigo": 30, "valor": "1000.00"},  # Saldo de Salário (provento)
            {"codigo": 33, "valor": "500.00"},   # Férias Vencidas (provento)
            {"codigo": 47, "valor": "100.00"},   # Previdência (desconto)
            {"codigo": 42, "valor": "80.00"},    # FGTS 8% (informativo: não entra no líquido)
        ],
    }


def test_rescisao_no_banco(tmp_path):
    engine = create_engine(
        f"sqlite:///{(tmp_path / 'teste.db').as_posix()}",
        connect_args={"check_same_thread": False},
    )
    SessionTeste = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    def get_db_teste():
        db = SessionTeste()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = get_db_teste
    client = TestClient(app)

    try:
        with SessionTeste() as db:
            colaborador = Colaborador(
                nome="Maria Teste",
                cpf="12345678909",
                email="maria@teste.com",
                cargo="Analista",
                empresa_id=1,
                salario=Decimal("1800.00"),
            )
            db.add(colaborador)
            db.commit()
            db.refresh(colaborador)
            colaborador_id = colaborador.id

        # 1) criar: totais calculados pelo servidor, empresa e salário vindos do colaborador
        resp = client.post("/rescisoes/", json=_dados(colaborador_id))
        assert resp.status_code == 201, resp.text
        rescisao = resp.json()
        assert rescisao["status"] == "EM_CONFERENCIA"
        assert rescisao["empresa_id"] == 1
        assert Decimal(rescisao["remuneracao"]) == Decimal("1800.00")
        assert Decimal(rescisao["total_proventos"]) == Decimal("1500.00")
        assert Decimal(rescisao["total_descontos"]) == Decimal("100.00")
        assert Decimal(rescisao["total_liquido"]) == Decimal("1400.00")
        assert [i["codigo"] for i in rescisao["itens"]] == [30, 33, 42, 47]
        rescisao_id = rescisao["id"]

        # 2) listar e detalhar (lendo de novo do banco)
        resp = client.get("/rescisoes/")
        assert resp.status_code == 200 and len(resp.json()) == 1
        resp = client.get(f"/rescisoes/{rescisao_id}")
        assert resp.status_code == 200 and len(resp.json()["itens"]) == 4

        # 3) corrigir: os itens antigos saem, os novos entram, os totais são recalculados
        resp = client.put(
            f"/rescisoes/{rescisao_id}",
            json=_dados(colaborador_id, itens=[{"codigo": 30, "valor": "2000.00"}]),
        )
        assert resp.status_code == 200, resp.text
        corrigida = resp.json()
        assert [i["codigo"] for i in corrigida["itens"]] == [30]
        assert Decimal(corrigida["total_liquido"]) == Decimal("2000.00")
        assert len(client.get(f"/rescisoes/{rescisao_id}").json()["itens"]) == 1

        # 4) erros previstos
        assert client.get("/rescisoes/9999").status_code == 404
        assert client.post("/rescisoes/", json=_dados(9999)).status_code == 404
        assert client.post("/rescisoes/", json=_dados(colaborador_id, causa="Qualquer coisa")).status_code == 400
        assert (
            client.post(
                "/rescisoes/", json=_dados(colaborador_id, itens=[{"codigo": 46, "valor": "10.00"}])
            ).status_code
            == 422  # 46 (total bruto) é calculado pelo sistema
        )

        # 5) envio: sem PDF gerado não pode enviar, e ainda não há tentativas registradas
        assert client.post(f"/rescisoes/{rescisao_id}/enviar").status_code == 400
        resp = client.get(f"/rescisoes/{rescisao_id}/envios")
        assert resp.status_code == 200 and resp.json() == []
        assert client.get("/rescisoes/9999/envios").status_code == 404
    finally:
        engine.dispose()
