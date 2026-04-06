from marymount.edu.receiptscanner.services.validation_service import ValidationService


def test_validation_allows_supported_extensions():
    assert ValidationService.is_allowed_filename("receipt.jpg", {"jpg", "jpeg", "png"})
    assert ValidationService.is_allowed_filename("receipt.PNG", {"jpg", "jpeg", "png"})


def test_validation_rejects_unsupported_extensions():
    assert not ValidationService.is_allowed_filename("receipt.pdf", {"jpg", "jpeg", "png"})
