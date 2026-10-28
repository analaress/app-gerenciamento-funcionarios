"""Envio de e-mail da rescisão: falha registrada e modo simulado (banco temporário)."""
from decimal import Decimal

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.models import rescisao as _modelos_rescisao  # noqa: F401  (registra as tabelas de rescisão)
from app.models.colaborador import Colaborador
from app.routers.rescisoes import router
from app.services import email_service, pdf_service, rescisao_service


def test_envio_de_email_falha_e_modo_simulado(tmp_path, monkeypatch):
    # PDF falso e pastas temporárias: o teste não escreve nada no projeto e não envia e-mail de verdade
    def pdf_falso(contexto, destino):
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(b"%PDF-1.4 teste")
        return destino

    monkeypatch.setattr(pdf_service, "gerar_pdf_rescisao", pdf_falso)
    monkeypatch.setattr(rescisao_service, "PASTA_PDFS", tmp_path / "pdfs")
    monkeypatch.setattr(email_service, "PASTA_EMAILS_SIMULADOS", tmp_path / "emails")

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

        dados = {
            "colaborador_id": colaborador_id,
            "data_desligamento": "2026-10-15",
            "causa_afastamento": "Demissão sem justa causa",
            "itens": [{"codigo": 30, "valor": "1000.00"}],
        }
        rescisao_id = client.post("/rescisoes/", json=dados).json()["id"]
        resp = client.post(f"/rescisoes/{rescisao_id}/gerar")
        assert resp.status_code == 200 and resp.json()["status"] == "GERADO", resp.text

        # 1) sem modo simulado e sem servidor de e-mail configurado: falha, e a falha fica registrada
        for nome in ("EMAIL_SIMULADO", "SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"):
            monkeypatch.delenv(nome, raising=False)
        resp = client.post(f"/rescisoes/{rescisao_id}/enviar")
        assert resp.status_code == 502, resp.text
        assert client.get(f"/rescisoes/{rescisao_id}").json()["status"] == "ERRO_ENVIO"
        envios = client.get(f"/rescisoes/{rescisao_id}/envios").json()
        assert len(envios) == 1
        assert envios[0]["sucesso"] is False and "configurado" in envios[0]["erro"]
        assert envios[0]["destinatario"] == "maria@teste.com"  # padrão: e-mail do colaborador

        # 2) modo simulado: reenviar funciona, grava um .eml e o status vira ENVIADO
        monkeypatch.setenv("EMAIL_SIMULADO", "true")
        resp = client.post(f"/rescisoes/{rescisao_id}/enviar")
        assert resp.status_code == 200 and resp.json()["status"] == "ENVIADO", resp.text
        envios = client.get(f"/rescisoes/{rescisao_id}/envios").json()
        assert [e["sucesso"] for e in envios] == [False, True]

        arquivos = list((tmp_path / "emails").glob("*.eml"))
        assert len(arquivos) == 1
        texto = arquivos[0].read_text(errors="ignore")
        assert "maria@teste.com" in texto and "rescisao_" in texto  # destinatário e PDF anexo

        # 3) destinatário informado na hora prevalece sobre o e-mail do cadastro
        resp = client.post(f"/rescisoes/{rescisao_id}/enviar", json={"destinatario": "outro@teste.com"})
        assert resp.status_code == 200
        assert any("outro@teste.com" in a.name for a in (tmp_path / "emails").glob("*.eml"))
    finally:
        engine.dispose()
