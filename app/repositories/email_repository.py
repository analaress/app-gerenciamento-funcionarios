from app.data import DATA_DIR
from app.repositories.json_repository import JsonRepository
from datetime import datetime
from itertools import count


_REGISTROS: list[dict] = []
_proximo_id = count(1)


class EmailRepository(JsonRepository):
    def __init__(self):
        super().__init__(DATA_DIR / "emails_enviados.json")


def registrar(
    documento_id: int,
    destinatario: str,
    status: str,
    erro: str | None = None,
    simulado: bool = False,
) -> dict:
    registro = {
        "id": next(_proximo_id),
        "documento_id": documento_id,
        "destinatario": destinatario,
        "status": status,
        "erro": erro,
        "simulado": simulado,
        "data_tentativa": datetime.now(),
    }
    _REGISTROS.append(registro)
    return registro


def listar_por_documento(documento_id: int) -> list[dict]:
    """Todas as tentativas de envio de um documento, da mais recente para a mais antiga."""
    return [r for r in reversed(_REGISTROS) if r["documento_id"] == documento_id]


def listar_todos() -> list[dict]:
    return list(reversed(_REGISTROS))
