"""Histórico de documentos no banco (SQLite temporário: o colaboradores.db NÃO é tocado)."""
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import historico_documento as _modelo_historico  # noqa: F401  (registra a tabela)
from app.repositories import historico_repository
from app.schemas.historico import HistoricoCriar, StatusDocumento, TipoDocumento
from app.services import historico_service


def _dados(nome, tipo="RESCISAO", status="GERADO", referencia=None, empresa="Alves e Filhos"):
    return HistoricoCriar(
        colaborador_nome=nome,
        colaborador_cpf="11144477735",
        empresa=empresa,
        tipo=tipo,
        status=status,
        referencia=referencia,
        usuario_responsavel="RH Operacional",
    )


def test_historico_no_banco(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{(tmp_path / 'historico.db').as_posix()}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(historico_repository, "SessionLocal", sessionmaker(bind=engine))

    try:
        # registrar: recibos e rescisões entram no mesmo histórico
        r1 = historico_service.registrar(_dados("Maria Souza", referencia="rescisao-1"))
        r2 = historico_service.registrar(
            _dados("João Álvares", tipo="RECIBO", status="ENVIADO", empresa="Cunha")
        )
        assert r1["id"] == 1 and r2["id"] == 2

        # os mais recentes primeiro, e os filtros de sempre
        assert [h["id"] for h in historico_service.listar()] == [2, 1]
        assert [h["id"] for h in historico_service.listar(tipo=TipoDocumento.RECIBO)] == [2]
        assert [h["id"] for h in historico_service.listar(status=StatusDocumento.GERADO)] == [1]
        assert [h["id"] for h in historico_service.listar(busca="ÁLVARES")] == [2]  # ignora maiúsculas
        assert [h["id"] for h in historico_service.listar(busca="cunha")] == [2]

        # atualizar status e data
        historico_repository.atualizar(1, status="ENVIADO", data_envio=date(2026, 11, 1))
        atualizado = historico_repository.buscar(1)
        assert atualizado["status"] == "ENVIADO" and atualizado["data_envio"] == date(2026, 11, 1)
        assert historico_repository.atualizar(999, status="GERADO") is None
        assert historico_repository.buscar(999) is None

        # resumo da tela
        resumo = historico_service.resumo()
        assert (resumo.pendentes, resumo.gerados, resumo.enviados, resumo.com_erro, resumo.total) == (0, 2, 2, 0, 2)

        # "reiniciar o servidor": uma sessão nova no mesmo arquivo continua vendo tudo
        monkeypatch.setattr(historico_repository, "SessionLocal", sessionmaker(bind=engine))
        assert len(historico_service.listar()) == 2
        assert historico_service.listar(busca="maria")[0]["referencia"] == "rescisao-1"
    finally:
        engine.dispose()
