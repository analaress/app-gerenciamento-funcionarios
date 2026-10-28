import json
import os
import tempfile
from threading import Lock
from pathlib import Path
from typing import Any


class JsonRepository:
    _locks: dict[Path, Lock] = {}

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = self._locks.setdefault(self.path.resolve(), Lock())

    def list(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            self._write([])
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def get_by_id(self, record_id: int) -> dict[str, Any] | None:
        return next((item for item in self.list() if item.get("id") == record_id), None)

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            records = self.list()
            record = {"id": max((item.get("id", 0) for item in records), default=0) + 1, **data}
            records.append(record)
            self._write(records)
            return record

    def update(self, record_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        with self._lock:
            records = self.list()
            for index, record in enumerate(records):
                if record.get("id") == record_id:
                    records[index] = {**record, **data, "id": record_id}
                    self._write(records)
                    return records[index]
            return None

    def delete(self, record_id: int) -> bool:
        with self._lock:
            records = self.list()
            filtered = [item for item in records if item.get("id") != record_id]
            if len(filtered) == len(records):
                return False
            self._write(filtered)
            return True

    def _write(self, records: list[dict[str, Any]]) -> None:
        payload = json.dumps(records, ensure_ascii=False, indent=2) + "\n"
        fd, temporary = tempfile.mkstemp(dir=self.path.parent, prefix=f".{self.path.name}.")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as output:
                output.write(payload)
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
