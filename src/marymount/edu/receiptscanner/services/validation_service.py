from __future__ import annotations

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


class ValidationService:
    @staticmethod
    def allowed_file(filename: str, allowed_extensions: set[str]) -> bool:
        return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions

    @classmethod
    def validate_upload(
        cls,
        uploaded_file: FileStorage | None,
        receipt_type: str,
        allowed_extensions: set[str],
        valid_receipt_types: list[str],
    ) -> tuple[bool, str]:
        if uploaded_file is None or not uploaded_file.filename:
            return False, "No file was provided."
        if not cls.allowed_file(uploaded_file.filename, allowed_extensions):
            return False, "Unsupported file type. Allowed types: .png, .jpg, .jpeg"
        if receipt_type not in valid_receipt_types:
            return False, "A valid receipt type is required."
        return True, secure_filename(uploaded_file.filename)
