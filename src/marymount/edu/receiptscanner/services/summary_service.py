from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from ..models import ReceiptRecord


class SummaryService:
    @staticmethod
    def monthly_summary(records: list[ReceiptRecord]) -> list[dict]:
        buckets: dict[str, list[ReceiptRecord]] = defaultdict(list)
        for record in records:
            if not record.summary_eligible:
                continue
            month_key = SummaryService._normalize_month(record.transaction_date) if record.transaction_date else "Unknown"
            buckets[month_key].append(record)

        results = []
        for month, items in sorted(buckets.items()):
            amounts = [r.total_amount for r in items if r.total_amount is not None]
            total = sum(amounts)
            avg = total / len(amounts) if amounts else 0.0
            results.append({
                "month": month,
                "count": len(items),
                "total": round(total, 2),
                "average": round(avg, 2),
            })
        return results

    @staticmethod
    def sidebar_metrics(records: list[ReceiptRecord]) -> dict[str, float | int]:
        eligible = [r for r in records if r.summary_eligible and r.total_amount is not None]
        total = round(sum(r.total_amount for r in eligible), 2) if eligible else 0.0
        count = len(eligible)
        average = round(total / count, 2) if count else 0.0
        return {"total": total, "average": average, "count": count}

    @staticmethod
    def available_months(records: list[ReceiptRecord]) -> list[str]:
        months = {SummaryService._normalize_month(r.transaction_date) for r in records if r.transaction_date}
        return sorted(months)

    @staticmethod
    def available_years(records: list[ReceiptRecord]) -> list[str]:
        years = {SummaryService._normalize_month(r.transaction_date)[:4] for r in records if r.transaction_date}
        return sorted(years)

    @staticmethod
    def _normalize_month(date_str: str) -> str:
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%m-%d-%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(date_str, fmt).strftime("%Y-%m")
            except ValueError:
                continue
        return "Unknown"
