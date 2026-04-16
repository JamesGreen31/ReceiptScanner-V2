from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from ..models import ReceiptRecord


class StorageService:
    @staticmethod
    def ensure_environment(config: dict) -> None:
        for key in ["UPLOAD_DIR", "PROCESSED_DIR", "OCR_LOG_DIR"]:
            Path(config[key]).mkdir(parents=True, exist_ok=True)
        Path(config["DATA_FILE"]).parent.mkdir(parents=True, exist_ok=True)
        if not Path(config["DATA_FILE"]).exists():
            Path(config["DATA_FILE"]).write_text("[]", encoding="utf-8")

    @staticmethod
    def load_records(data_file: str) -> list[ReceiptRecord]:
        path = Path(data_file)
        raw = json.loads(path.read_text(encoding="utf-8"))
        return [ReceiptRecord.from_dict(item) for item in raw]

    @staticmethod
    def save_records(data_file: str, records: Iterable[ReceiptRecord]) -> None:
        payload = [record.to_dict() for record in records]
        Path(data_file).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def upsert_record(cls, data_file: str, record: ReceiptRecord) -> None:
        records = cls.load_records(data_file)
        for idx, existing in enumerate(records):
            if existing.receipt_id == record.receipt_id:
                records[idx] = record
                cls.save_records(data_file, records)
                return
        records.append(record)
        cls.save_records(data_file, records)

    @classmethod
    def get_record(cls, data_file: str, receipt_id: str) -> ReceiptRecord | None:
        return next((r for r in cls.load_records(data_file) if r.receipt_id == receipt_id), None)

    @classmethod
    def delete_record(cls, data_file: str, receipt_id: str) -> ReceiptRecord | None:
        records = cls.load_records(data_file)
        kept: list[ReceiptRecord] = []
        deleted: ReceiptRecord | None = None
        for record in records:
            if record.receipt_id == receipt_id:
                deleted = record
            else:
                kept.append(record)
        cls.save_records(data_file, kept)
        return deleted

    @classmethod
    def clear_all(cls, data_file: str) -> None:
        cls.save_records(data_file, [])

    @classmethod
    def collection_names(cls, data_file: str) -> list[str]:
        names = {record.collection_name for record in cls.load_records(data_file) if record.collection_name}
        names.add("Default")
        return sorted(names)

    @staticmethod
    def filter_records(
        records: list[ReceiptRecord],
        collection_name: str | None = None,
        category: str | None = None,
        query: str | None = None,
    ) -> list[ReceiptRecord]:
        filtered = records
        if collection_name and collection_name != "all":
            filtered = [r for r in filtered if r.collection_name == collection_name]
        if category and category != "all":
            filtered = [r for r in filtered if r.receipt_type == category]
        if query:
            q = query.lower().strip()
            filtered = [
                r for r in filtered
                if q in (r.filename or "").lower()
                or q in (r.collection_name or "").lower()
                or q in (r.receipt_type or "").lower()
                or q in (r.merchant or "").lower()
                or q in (r.transaction_date or "").lower()
                or q in (r.raw_ocr_text or "").lower()
            ]
        return filtered
