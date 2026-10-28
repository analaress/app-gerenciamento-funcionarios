from collections import Counter
from datetime import date
from itertools import count

_REGISTROS: list[dict] = []

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
