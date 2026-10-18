from app.data import DATA_DIR
from app.repositories.json_repository import JsonRepository


class ColaboradorRepository(JsonRepository):
    def __init__(self):
        super().__init__(DATA_DIR / "colaboradores.json")

    def list_by_empresa(self, empresa_id: int):
        return [item for item in self.list() if item.get("empresa_id") == empresa_id]
