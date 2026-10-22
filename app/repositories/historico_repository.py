from collections import Counter
from datetime import date
from itertools import count

# Dados Mockados
_REGISTROS = [
    {
        "id": 1,
        "colaborador_nome": "Ana Exemplo",
        "colaborador_cpf": "000.000.000-01",
        "empresa": "Empresa Alfa Ltda",
        "tipo": "RECIBO",
        "status": "ENVIADO",
        "referencia": "Agosto/2026",
        "data_geracao": date(2026, 9, 3),
        "data_envio": date(2026, 9, 4),
        "usuario_responsavel": "RH Operacional",
    },
    {
        "id": 2,
        "colaborador_nome": "Bruno Modelo",
        "colaborador_cpf": "000.000.000-02",
        "empresa": "Empresa Beta S.A.",
        "tipo": "RECIBO",
        "status": "GERADO",
        "referencia": "Agosto/2026",
        "data_geracao": date(2026, 9, 5),
        "data_envio": None,
        "usuario_responsavel": "RH Operacional",
    },
    {
        "id": 3,
        "colaborador_nome": "Carla Teste",
        "colaborador_cpf": "000.000.000-03",
        "empresa": "Empresa Alfa Ltda",
        "tipo": "RESCISAO",
        "status": "EM_CONFERENCIA",
        "referencia": "Pedido de demissão",
        "data_geracao": None,
        "data_envio": None,
        "usuario_responsavel": "Administrativo",
    },
    {
        "id": 4,
        "colaborador_nome": "Diego Fictício",
        "colaborador_cpf": "000.000.000-04",
        "empresa": "Empresa Gama ME",
        "tipo": "RECIBO",
        "status": "ERRO_ENVIO",
        "referencia": "Agosto/2026",
        "data_geracao": date(2026, 9, 5),
        "data_envio": None,
        "usuario_responsavel": "RH Operacional",
    },
    {
        "id": 5,
        "colaborador_nome": "Elisa Amostra",
        "colaborador_cpf": "000.000.000-05",
        "empresa": "Empresa Beta S.A.",
        "tipo": "RESCISAO",
        "status": "PENDENTE",
        "referencia": "Sem justa causa",
        "data_geracao": None,
        "data_envio": None,
        "usuario_responsavel": "Administrativo",
    },
]

_proximo_id = count(len(_REGISTROS) + 1)


def listar(busca: str | None = None, tipo: str | None = None, status: str | None = None):
    termo = busca.lower() if busca else None
    resultado = []
    for r in reversed(_REGISTROS):  # os mais recentes primeiro
        if tipo and r["tipo"] != tipo:
            continue
        if status and r["status"] != status:
            continue
        if termo:
            texto = f'{r["colaborador_nome"]} {r["colaborador_cpf"]} {r["empresa"]}'.lower()
            if termo not in texto:
                continue
        resultado.append(r)
    return resultado


def contar_por_status() -> Counter:
    return Counter(r["status"] for r in _REGISTROS)


def criar(dados: dict) -> dict:
    registro = {"id": next(_proximo_id), **dados}
    _REGISTROS.append(registro)
    return registro


def buscar(documento_id: int) -> dict | None:
    return next((r for r in _REGISTROS if r["id"] == documento_id), None)


def atualizar(documento_id: int, **campos) -> dict | None:
    registro = buscar(documento_id)
    if registro:
        registro.update(campos)
    return registro