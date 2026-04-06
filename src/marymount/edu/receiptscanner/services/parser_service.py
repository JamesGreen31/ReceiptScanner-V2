from __future__ import annotations

import re
from datetime import datetime
from typing import Any


class ParserService:
    VENDOR_WHITELIST = ["SHELL", "BP", "EXXON", "MOBIL", "COSTCO", "WALMART", "TARGET"]
    DATE_PATTERNS = [
        re.compile(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b"),
        re.compile(r"\b(\d{4}-\d{2}-\d{2})\b"),
        re.compile(r"\b(\d{4}/\d{1,2}/\d{1,2})\b"),
        re.compile(r"\b([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})\b"),
        re.compile(r"\b(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\b"),
    ]
    MONEY_PATTERN = re.compile(r"(?<![\d/])\$?\s*([0-9]+(?:,[0-9]{3})*(?:[.][0-9]{2,4}))\b")

    @classmethod
    def parse(cls, text: str, receipt_type: str) -> dict[str, Any]:
        clean_text = text or ""
        review_reasons: list[str] = []

        if not clean_text.strip() or "disabled" in clean_text.lower():
            return {
                "merchant": None,
                "transaction_date": None,
                "total_amount": None,
                "receipt_type": receipt_type,
                "status": "broken",
                "raw_ocr_text": clean_text,
                "review_reasons": ["ocr_unavailable" if "disabled" in clean_text.lower() else "empty_ocr_text"],
            }

        merchant = cls._extract_merchant(clean_text)
        transaction_date = cls._extract_date(clean_text)
        total_amount = cls._extract_total(clean_text)

        if transaction_date is None:
            review_reasons.append("missing_date")
        if total_amount is None:
            review_reasons.append("missing_total")

        status = "valid" if not review_reasons else "needs_review"
        return {
            "merchant": merchant,
            "transaction_date": transaction_date,
            "total_amount": total_amount,
            "receipt_type": receipt_type,
            "status": status,
            "raw_ocr_text": clean_text,
            "review_reasons": review_reasons,
        }

    @classmethod
    def _extract_merchant(cls, text: str) -> str | None:
        upper_text = text.upper()
        merchant = next((v.title() for v in cls.VENDOR_WHITELIST if v in upper_text), None)
        if merchant:
            return merchant

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        skip_tokens = {
            "TOTAL", "SUBTOTAL", "TAX", "CHANGE", "CASH", "VISA", "MASTERCARD", "RECEIPT",
            "THANK", "DATE", "TIME", "AMOUNT", "BALANCE", "SALE", "ITEM", "QTY",
        }
        for line in lines[:6]:
            normalized = re.sub(r"[^A-Za-z &'\-]", "", line).strip()
            if len(normalized) < 3:
                continue
            upper = normalized.upper()
            if any(token in upper for token in skip_tokens):
                continue
            if sum(char.isalpha() for char in normalized) < 3:
                continue
            return normalized[:80]
        return None

    @classmethod
    def _extract_date(cls, text: str) -> str | None:
        for pattern in cls.DATE_PATTERNS:
            match = pattern.search(text)
            if not match:
                continue
            parsed = cls._normalize_date(match.group(1))
            if parsed:
                return parsed
        return None

    @staticmethod
    def _normalize_date(date_str: str) -> str | None:
        candidates = [
            "%m/%d/%Y", "%m/%d/%y", "%m-%d-%Y", "%m-%d-%y", "%Y-%m-%d", "%Y/%m/%d",
            "%b %d %Y", "%b %d, %Y", "%B %d %Y", "%B %d, %Y", "%d %b %Y", "%d %B %Y",
        ]
        compact = re.sub(r"\s+", " ", date_str.replace(",", ", ")).strip()
        compact = re.sub(r"\s+,", ",", compact)
        for fmt in candidates:
            try:
                return datetime.strptime(compact, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None

    @classmethod
    def _extract_total(cls, text: str) -> float | None:
        amounts: list[float] = []
        for match in cls.MONEY_PATTERN.finditer(text):
            candidate = match.group(1).replace(",", "")
            try:
                amounts.append(round(float(candidate), 2))
            except ValueError:
                continue
        return max(amounts) if amounts else None
