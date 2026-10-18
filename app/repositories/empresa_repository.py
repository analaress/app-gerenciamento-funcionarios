from app.data import DATA_DIR
from app.repositories.json_repository import JsonRepository


class EmpresaRepository(JsonRepository):
    def __init__(self):
        super().__init__(DATA_DIR / "empresas.json")
