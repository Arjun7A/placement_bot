import json
import logging
from pathlib import Path


class JobIdStore:
    def __init__(self, file_path: str, max_items: int = 0) -> None:
        self.file_path = Path(file_path)
        self.max_items = max_items
        self._ids = self._load()

    @property
    def size(self) -> int:
        return len(self._ids)

    def has(self, job_id: str) -> bool:
        return job_id in self._ids

    def add(self, job_id: str) -> bool:
        if not job_id or job_id in self._ids:
            return False

        self._ids.add(job_id)
        self._persist()
        return True

    def _load(self) -> set[str]:
        if not self.file_path.exists():
            return set()

        try:
            raw_data = json.loads(self.file_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logging.warning("Failed to read job-id store '%s': %s", self.file_path, exc)
            return set()

        if not isinstance(raw_data, list):
            logging.warning(
                "Invalid job-id store format in '%s'; expected JSON list",
                self.file_path,
            )
            return set()

        return {str(item).strip() for item in raw_data if str(item).strip()}

    def _persist(self) -> None:
        ids_to_store = sorted(self._ids)
        if self.max_items > 0 and len(ids_to_store) > self.max_items:
            ids_to_store = ids_to_store[-self.max_items :]

        tmp_path = self.file_path.with_suffix(f"{self.file_path.suffix}.tmp")
        try:
            tmp_path.write_text(json.dumps(ids_to_store, ensure_ascii=True), encoding="utf-8")
            tmp_path.replace(self.file_path)
        except OSError as exc:
            logging.warning("Failed to write job-id store '%s': %s", self.file_path, exc)
