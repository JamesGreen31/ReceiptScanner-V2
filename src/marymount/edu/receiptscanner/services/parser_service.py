from __future__ import annotations

import re
from datetime import datetime
from typing import Any


class ParserService:
    VENDOR_WHITELIST = [
    # Gas Stations / Fuel
    "SHELL", "BP", "EXXON", "MOBIL", "CHEVRON", "TEXACO", "CITGO", "SUNOCO",
    "VALERO", "ARCO", "PHILLIPS 66", "CONOCO", "MARATHON", "SPEEDWAY",
    "LOVE'S", "PILOT", "FLYING J", "CIRCLE K", "7-ELEVEN", "WAWA",
    "SHEETZ", "QUIKTRIP", "RACETRAC", "KUM & GO", "AMPM",

    # Big Box / Retail
    "WALMART", "TARGET", "COSTCO", "SAM'S CLUB", "BJ'S", "MEIJER",
    "FRED MEYER", "KROGER", "ALDI", "LIDL", "WHOLE FOODS", "TRADER JOE'S",
    "PUBLIX", "SAFEWAY", "GIANT", "GIANT EAGLE", "HARRIS TEETER",
    "FOOD LION", "WINCO", "SPROUTS", "WEGMANS", "STOP & SHOP",

    # Pharmacies / Convenience
    "CVS", "CVS PHARMACY", "WALGREENS", "RITE AID", "DUANE READE",

    # Fast Food
    "MCDONALD'S", "BURGER KING", "WENDY'S", "TACO BELL", "KFC",
    "CHICK-FIL-A", "SUBWAY", "DOMINO'S", "PIZZA HUT", "PAPA JOHN'S",
    "LITTLE CAESARS", "ARBY'S", "JACK IN THE BOX", "SONIC", "FIVE GUYS",
    "IN-N-OUT", "CHIPOTLE", "QDOBA", "PANERA", "ZAXBY'S",

    # Coffee / Cafe
    "STARBUCKS", "DUNKIN", "DUNKIN DONUTS", "PEET'S", "CARIBOU COFFEE",
    "TIM HORTONS",

    # Restaurants (Casual Dining)
    "APPLEBEE'S", "CHILI'S", "OLIVE GARDEN", "RED LOBSTER",
    "OUTBACK", "TGI FRIDAYS", "BUFFALO WILD WINGS",
    "CRACKER BARREL", "IHOP", "DENNY'S",

    # Online / Tech Retail
    "AMAZON", "AMAZON.COM", "EBAY", "BEST BUY", "NEWEGG", "MICROCENTER",

    # Department / Clothing
    "MACY'S", "KOHL'S", "JCPENNEY", "NORDSTROM", "OLD NAVY",
    "GAP", "H&M", "ZARA", "TJ MAXX", "MARSHALLS", "ROSS",

    # Home Improvement
    "HOME DEPOT", "LOWE'S", "MENARDS", "ACE HARDWARE", "TRUE VALUE",

    # Auto / Parts / Service
    "AUTOZONE", "ADVANCE AUTO PARTS", "O'REILLY", "PEP BOYS",
    "FIRESTONE", "GOODYEAR", "Jiffy Lube",

    # Travel / Lodging
    "MARRIOTT", "HILTON", "HYATT", "HOLIDAY INN", "BEST WESTERN",
    "MOTEL 6", "SUPER 8",

    # Airlines / Transport
    "DELTA", "AMERICAN AIRLINES", "UNITED", "SOUTHWEST",
    "UBER", "LYFT",

    # Misc Common
    "DOLLAR GENERAL", "FAMILY DOLLAR", "DOLLAR TREE",
    "BIG LOTS", "OFFICE DEPOT", "STAPLES",
    "PETSMART", "PETCO",
    "GAMESTOP",
    "SEARS"
    ]
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
        try:
            if total_amount > 1000:
                review_reasons.append("high_total")
            if total_amount <= 0:
                review_reasons.append("non_positive_total")
        except:
            review_reasons.append("Total either not found or not an integer")

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
