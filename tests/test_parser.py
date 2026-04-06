from marymount.edu.receiptscanner.services.parser_service import ParserService


def test_parser_extracts_largest_total_when_multiple_amounts_exist():
    text = """
    STORE\n
    Subtotal 12.50
    Tax 1.25
    Total 13.75
    Cashback 40.00
    """
    parsed = ParserService.parse(text, "retail")
    assert parsed["total_amount"] == 40.00


def test_parser_marks_needs_review_when_date_missing():
    text = "TOTAL $15.80"
    parsed = ParserService.parse(text, "gas")
    assert parsed["status"] == "needs_review"
    assert "missing_date" in parsed["review_reasons"]



def test_parser_accepts_three_decimal_currency_and_rounds():
    text = """EXXON MOBIL
01/09/2026
$168.730
12.0932 g @ $2.903 /g"""
    parsed = ParserService.parse(text, "gas")
    assert parsed["total_amount"] == 168.73
    assert parsed["transaction_date"] == "2026-01-09"
