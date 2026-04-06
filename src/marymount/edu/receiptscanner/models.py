from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any
import uuid


@dataclass
class ReceiptRecord:
    receipt_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    filename: str = ""
    processed_filename: str | None = None
    collection_name: str = "Default"
    receipt_type: str = "other"
    merchant: str | None = None
    transaction_date: str | None = None
    total_amount: float | None = None
    raw_ocr_text: str = ""
    status: str = "uploaded"
    review_reasons: list[str] = field(default_factory=list)
    error_message: str | None = None
    include_in_summary: bool = True
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def summary_eligible(self) -> bool:
        return self.status == "valid" and self.include_in_summary

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReceiptRecord":
        payload = dict(data)
        payload.setdefault("collection_name", "Default")
        payload.setdefault("include_in_summary", True)
        payload.setdefault("review_reasons", [])
        return cls(**payload)
