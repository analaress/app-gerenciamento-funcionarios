from app.data import DATA_DIR
from app.repositories.json_repository import JsonRepository


class EmailRepository(JsonRepository):
    def __init__(self):
        super().__init__(DATA_DIR / "emails_enviados.json")
