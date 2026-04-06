from __future__ import annotations

import csv
from io import StringIO

from ..models import ReceiptRecord


class ExportService:
    @staticmethod
    def to_csv(records: list[ReceiptRecord]) -> str:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "receipt_id",
            "collection_name",
            "filename",
            "receipt_type",
            "merchant",
            "transaction_date",
            "total_amount",
            "status",
            "include_in_summary",
            "summary_eligible",
        ])
        for record in records:
            writer.writerow([
                record.receipt_id,
                record.collection_name,
                record.filename,
                record.receipt_type,
                record.merchant,
                record.transaction_date,
                record.total_amount,
                record.status,
                record.include_in_summary,
                record.summary_eligible,
            ])
        return output.getvalue()
