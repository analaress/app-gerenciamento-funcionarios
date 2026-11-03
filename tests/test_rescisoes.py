"""Rescisão com banco (SQLite temporário: o colaboradores.db NÃO é tocado)."""
from datetime import date
from decimal import Decimal

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.models import empresa as _modelo_empresa  # noqa: F401  (registra as tabelas)
from app.models import historico_documento as _modelo_historico  # noqa: F401
from app.models import rescisao as _modelo_rescisao  # noqa: F401
from app.models.colaborador import Colaborador
from app.models.empresa import Empresa
from app.repositories import historico_repository
from app.routers.rescisoes import router
from app.services import email_service, historico_service, rescisao_service


def _montar(tmp_path, monkeypatch):
    """App de teste com banco temporário, uma empresa e uma colaboradora."""
    engine = create_engine(
        f"sqlite:///{(tmp_path / 'teste.db').as_posix()}",
        connect_args={"check_same_thread": False},
    )
    Sessao = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    # o histórico de documentos também vai para o banco temporário do teste
    monkeypatch.setattr(historico_repository, "SessionLocal", Sessao)

    def get_db_teste():
        db = Sessao()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = get_db_teste

    with Sessao() as db:
        empresa = Empresa(
            razao_social="Alves e Filhos Ltda", nome_fantasia="Alves e Filhos", cnpj="11.222.333/0001-81",
            email="contato@alves.example.com", telefone="(11) 3333-0001", cep="01310-100",
            logradouro="Av. Principal", numero="500", bairro="Industrial", cidade="São Paulo", estado="SP",
        )
        db.add(empresa)
        db.commit()
        db.refresh(empresa)
        colaboradora = Colaborador(
            nome="Maria Souza Teste", cpf="11144477735", email="maria@teste.example", cargo="Analista",
            empresa_id=empresa.id, salario=Decimal("3800.00"), situacao="ATIVO", data_admissao=date(2023, 6, 23),
            pis_pasep="123.45678.90-1", logradouro="Rua das Flores, 100", bairro="Centro", municipio="São Paulo",
            uf="SP", cep="01000-000", ctps="1234567 - 0001 / SP", data_nascimento=date(1990, 10, 30),
            nome_mae="Ana Souza",
        )
        desligado = Colaborador(
            nome="Joao Desligado", cpf="52998224725", email="joao@teste.example", cargo="Auxiliar",
            empresa_id=empresa.id, salario=Decimal("2000.00"), situacao="DESLIGADO",
        )
        db.add_all([colaboradora, desligado])
        db.commit()
        db.refresh(colaboradora)
        db.refresh(desligado)
        return engine, TestClient(app), colaboradora.id, desligado.id


def _situacao(engine, colaborador_id):
    with sessionmaker(bind=engine)() as db:
        return db.get(Colaborador, colaborador_id).situacao


def _dados(colaborador_id, itens=None, causa="Demissão sem justa causa"):
    return {
        "colaborador_id": colaborador_id,
        "data_desligamento": "2026-10-15",
        "causa_afastamento": causa,
        "itens": itens
        or [
            {"codigo": 30, "valor": "1000.00", "referencia": "15"},  # Saldo de Salário (provento)
            {"codigo": 33, "valor": "500.00"},                       # Férias Vencidas (provento)
            {"codigo": 47, "valor": "100.00"},                       # Previdência (desconto)
            {"codigo": 42, "valor": "80.00"},                        # FGTS 8% (informativo: fora do líquido)
        ],
    }


def test_rescisao_fluxo_completo(tmp_path, monkeypatch):
    monkeypatch.setattr(rescisao_service, "PASTA_PDFS", tmp_path / "pdfs")
    engine, client, colaboradora_id, desligado_id = _montar(tmp_path, monkeypatch)
    try:
        # 1) criar: totais calculados pelo servidor; empresa e salário vêm do colaborador
        resp = client.post("/rescisoes", json=_dados(colaboradora_id))
        assert resp.status_code == 201, resp.text
        rescisao = resp.json()
        assert rescisao["status"] == "EM_CONFERENCIA" and rescisao["empresa_id"] == 1
        assert Decimal(rescisao["remuneracao"]) == Decimal("3800.00")
        assert Decimal(rescisao["total_proventos"]) == Decimal("1500.00")
        assert Decimal(rescisao["total_descontos"]) == Decimal("100.00")
        assert Decimal(rescisao["total_liquido"]) == Decimal("1400.00")
        assert [i["codigo"] for i in rescisao["itens"]] == [30, 33, 42, 47]
        assert [i["id"] for i in rescisao["itens"]] == [1, 2, 3, 4]
        rescisao_id = rescisao["id"]
        historico = historico_service.listar()
        assert len(historico) == 1 and historico[0]["tipo"] == "RESCISAO"
        assert historico[0]["status"] == "EM_CONFERENCIA" and historico[0]["colaborador_nome"] == "Maria Souza Teste"

        # 2) listar e detalhar
        assert len(client.get("/rescisoes").json()) == 1
        assert client.get(f"/rescisoes/{rescisao_id}").json()["total_liquido"] == "1400.00"

        # 3) corrigir: os itens antigos saem, os novos entram, os totais são recalculados
        resp = client.put(f"/rescisoes/{rescisao_id}", json=_dados(colaboradora_id, itens=[{"codigo": 30, "valor": "2000.00"}]))
        assert resp.status_code == 200, resp.text
        assert [i["codigo"] for i in resp.json()["itens"]] == [30]
        assert Decimal(resp.json()["total_liquido"]) == Decimal("2000.00")

        # 4) erros previstos
        assert client.get("/rescisoes/9999").status_code == 404
        assert client.post("/rescisoes", json=_dados(9999)).status_code == 404
        assert client.post("/rescisoes", json=_dados(desligado_id)).status_code == 400  # já desligado
        resp = client.post("/rescisoes", json=_dados(colaboradora_id))  # a colaboradora já tem a rescisão #1
        assert resp.status_code == 400 and "já tem a rescisão" in resp.json()["detail"], resp.text
        assert len(client.get("/rescisoes").json()) == 1
        assert client.post("/rescisoes", json=_dados(colaboradora_id, causa="Qualquer coisa")).status_code == 400
        assert client.post("/rescisoes", json=_dados(colaboradora_id, itens=[{"codigo": 46, "valor": "10.00"}])).status_code == 422
        assert client.get(f"/rescisoes/{rescisao_id}/pdf").status_code == 409  # ainda não gerado

        # 5) gerar o PDF de verdade e baixar
        resp = client.post(f"/rescisoes/{rescisao_id}/gerar")
        assert resp.status_code == 200 and resp.json()["status"] == "GERADO", resp.text
        historico = historico_service.listar()
        assert len(historico) == 1 and historico[0]["status"] == "GERADO" and historico[0]["data_geracao"] is not None
        pdf = client.get(f"/rescisoes/{rescisao_id}/pdf")
        assert pdf.status_code == 200 and pdf.headers["content-type"] == "application/pdf"
        assert pdf.content.startswith(b"%PDF")
        assert client.post(f"/rescisoes/{rescisao_id}/gerar").status_code == 400  # já gerado

        # 6) corrigir depois de gerado: volta para EM_CONFERENCIA e o PDF antigo deixa de valer
        resp = client.put(f"/rescisoes/{rescisao_id}", json=_dados(colaboradora_id))
        assert resp.json()["status"] == "EM_CONFERENCIA"
        assert client.get(f"/rescisoes/{rescisao_id}/pdf").status_code == 409
        assert historico_service.listar()[0]["status"] == "EM_CONFERENCIA"
    finally:
        engine.dispose()


def test_envio_de_email_falha_e_modo_simulado(tmp_path, monkeypatch):
    monkeypatch.setattr(rescisao_service, "PASTA_PDFS", tmp_path / "pdfs")
    monkeypatch.setattr(email_service, "PASTA_EMAILS_SIMULADOS", tmp_path / "emails")
    monkeypatch.setattr(email_service, "_arquivo_env", lambda: {})  # ignora o .env de verdade
    for nome in ("EMAIL_SIMULADO", "SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM"):
        monkeypatch.delenv(nome, raising=False)

    engine, client, colaboradora_id, _ = _montar(tmp_path, monkeypatch)
    try:
        rescisao_id = client.post("/rescisoes", json=_dados(colaboradora_id)).json()["id"]

        # sem PDF gerado não dá para enviar
        assert client.post(f"/rescisoes/{rescisao_id}/enviar").status_code == 400
        assert client.get(f"/rescisoes/{rescisao_id}/envios").json() == []
        assert client.get("/rescisoes/9999/envios").status_code == 404

        assert client.post(f"/rescisoes/{rescisao_id}/gerar").status_code == 200

        # a tela pergunta se o e-mail está em modo de teste, para avisar a pessoa
        assert client.get("/rescisoes/email-modo").json() == {"simulado": False}

        # 1) sem modo simulado e sem servidor de e-mail configurado: falha, e a falha fica registrada
        resp = client.post(f"/rescisoes/{rescisao_id}/enviar")
        assert resp.status_code == 502, resp.text
        assert client.get(f"/rescisoes/{rescisao_id}").json()["status"] == "ERRO_ENVIO"
        envios = client.get(f"/rescisoes/{rescisao_id}/envios").json()
        assert len(envios) == 1 and envios[0]["sucesso"] is False and "configurado" in envios[0]["erro"]
        assert envios[0]["destinatario"] == "maria@teste.example"  # padrão: e-mail do colaborador
        assert historico_service.listar()[0]["status"] == "ERRO_ENVIO"
        assert _situacao(engine, colaboradora_id) == "ATIVO"  # envio com falha NÃO desliga

        # 2) modo simulado: reenviar funciona, grava um .eml e o status vira ENVIADO
        monkeypatch.setenv("EMAIL_SIMULADO", "true")
        assert client.get("/rescisoes/email-modo").json() == {"simulado": True}
        resp = client.post(f"/rescisoes/{rescisao_id}/enviar")
        assert resp.status_code == 200 and resp.json()["status"] == "ENVIADO", resp.text
        assert [e["sucesso"] for e in client.get(f"/rescisoes/{rescisao_id}/envios").json()] == [False, True]
        assert _situacao(engine, colaboradora_id) == "DESLIGADO"  # envio com sucesso desliga o colaborador
        assert client.post("/rescisoes", json=_dados(colaboradora_id)).status_code == 400  # sem documento novo
        historico = historico_service.listar()
        assert len(historico) == 1 and historico[0]["status"] == "ENVIADO"
        assert historico[0]["data_envio"] == date.today() and historico[0]["data_geracao"] == date.today()
        arquivos = list((tmp_path / "emails").glob("*.eml"))
        assert len(arquivos) == 1
        texto = arquivos[0].read_text(errors="ignore")
        assert "maria@teste.example" in texto and "rescisao_" in texto  # destinatário e PDF anexo

        # e-mail com formato inválido: 400, sem tentar enviar e sem registrar envio
        antes = len(client.get(f"/rescisoes/{rescisao_id}/envios").json())
        for ruim in ("sem-arroba", "a@b", "nome@@empresa.com", "nome sobrenome@empresa.com"):
            resp = client.post(f"/rescisoes/{rescisao_id}/enviar", json={"destinatario": ruim})
            assert resp.status_code == 400 and "válido" in resp.json()["detail"], (ruim, resp.text)
        assert len(client.get(f"/rescisoes/{rescisao_id}/envios").json()) == antes

        # 3) destinatário informado na hora prevalece sobre o e-mail do cadastro
        resp = client.post(f"/rescisoes/{rescisao_id}/enviar", json={"destinatario": "outro@teste.example"})
        assert resp.status_code == 200

        # 4) mesmo com o colaborador desligado, esta rescisão ainda pode ser corrigida, gerada e reenviada
        assert client.put(f"/rescisoes/{rescisao_id}", json=_dados(colaboradora_id)).status_code == 200
        assert client.post(f"/rescisoes/{rescisao_id}/gerar").status_code == 200
        assert client.post(f"/rescisoes/{rescisao_id}/enviar").status_code == 200
        assert client.get(f"/rescisoes/{rescisao_id}/pdf").status_code == 200
        assert any("outro@teste.example" in a.name for a in (tmp_path / "emails").glob("*.eml"))
    finally:
        engine.dispose()


def test_verbas_41_e_45_no_liquido_e_sugestao_de_valores(tmp_path, monkeypatch):
    monkeypatch.setattr(rescisao_service, "PASTA_PDFS", tmp_path / "pdfs")
    engine, client, _, _ = _montar(tmp_path, monkeypatch)
    try:
        with sessionmaker(bind=engine)() as db:  # um colaborador ativo com admissão, para as sugestões
            carlos = Colaborador(
                nome="Carlos Ativo", cpf="86288366757", email="carlos@teste.example", cargo="Motorista",
                empresa_id=1, salario=Decimal("3000.00"), situacao="ATIVO", data_admissao=date(2024, 2, 10),
            )
            db.add(carlos)
            db.commit()
            db.refresh(carlos)
            carlos_id = carlos.id

        # as verbas 41 e 45 entram no líquido (descontam); o FGTS (42) continua fora
        tipos = {v["codigo"]: v["tipo"] for v in client.get("/rescisoes/verbas-sugeridas").json()}
        assert tipos[41] == tipos[45] == "DESCONTO" and tipos[42] == tipos[43] == tipos[44] == "INFORMATIVO"
        itens = [
            {"codigo": 30, "valor": "1000.00"}, {"codigo": 41, "valor": "100.00"}, {"codigo": 45, "valor": "50.00"},
            {"codigo": 47, "valor": "100.00"}, {"codigo": 42, "valor": "80.00"},
        ]
        resp = client.post("/rescisoes", json=_dados(carlos_id, itens=itens))
        assert resp.status_code == 201, resp.text
        assert [Decimal(resp.json()[c]) for c in ("total_proventos", "total_descontos", "total_liquido")] == [
            Decimal("1000.00"), Decimal("250.00"), Decimal("750.00"),
        ]

        # sugestão de valores: saldo, 13º, férias proporcionais (+1/3) e FGTS 8%, sempre editáveis
        corpo = {"colaborador_id": carlos_id, "data_desligamento": "2026-10-15", "causa_afastamento": "Demissão sem justa causa"}
        resp = client.post("/rescisoes/sugestao", json=corpo)
        assert resp.status_code == 200, resp.text
        sugeridos = {i["codigo"]: (i["valor"], i["referencia"]) for i in resp.json()["itens"]}
        assert sugeridos == {
            30: ("1500.00", "15"), 31: ("2500.00", "10"), 35: ("2000.00", "8"), 36: ("666.67", None), 42: ("320.00", None),
        }
        assert all(i["explicacao"] for i in resp.json()["itens"]) and resp.json()["avisos"]

        # com a remuneração digitada no formulário, ela é a base (e não o salário do cadastro)
        resp = client.post("/rescisoes/sugestao", json={**corpo, "remuneracao": "2500.00"})
        assert resp.status_code == 200, resp.text
        assert {i["codigo"]: i["valor"] for i in resp.json()["itens"]} == {
            30: "1250.00", 31: "2083.33", 35: "1666.67", 36: "555.56", 42: "266.67",
        }
        assert "remuneração informada" in resp.json()["avisos"][0]

        corpo["causa_afastamento"] = "Demissão por justa causa"  # justa causa: sem 13º nem férias
        assert [i["codigo"] for i in client.post("/rescisoes/sugestao", json=corpo).json()["itens"]] == [30, 42]

        assert client.post("/rescisoes/sugestao", json={**corpo, "causa_afastamento": "Qualquer coisa"}).status_code == 400
        assert client.post("/rescisoes/sugestao", json={**corpo, "colaborador_id": 9999}).status_code == 404
    finally:
        engine.dispose()
