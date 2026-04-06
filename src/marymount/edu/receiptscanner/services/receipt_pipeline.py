from __future__ import annotations

from datetime import datetime
from pathlib import Path

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from ..models import ReceiptRecord
from .ocr_service import OCRService
from .parser_service import ParserService
from .preprocessing_service import PreprocessingService
from .storage_service import StorageService
from .validation_service import ValidationService


class ReceiptPipeline:
    def __init__(self, app_config: dict):
        self.config = app_config
        self.upload_dir = Path(app_config["UPLOAD_DIR"])
        self.processed_dir = Path(app_config["PROCESSED_DIR"])
        self.ocr_log_dir = Path(app_config["OCR_LOG_DIR"])
        self.ocr_service = OCRService(app_config["USE_OCR"], self.ocr_log_dir)

    def process_upload(self, uploaded_file: FileStorage, receipt_type: str, collection_name: str = "Default") -> ReceiptRecord:
        is_valid, detail = ValidationService.validate_upload(
            uploaded_file,
            receipt_type,
            self.config["ALLOWED_EXTENSIONS"],
            self.config["RECEIPT_TYPES"],
        )
        if not is_valid:
            return ReceiptRecord(
                filename=uploaded_file.filename if uploaded_file else "",
                collection_name=collection_name,
                receipt_type=receipt_type,
                status="broken",
                error_message=detail,
                review_reasons=["invalid_upload"],
                include_in_summary=False,
            )

        safe_name = secure_filename(detail)
        source_path = self.upload_dir / safe_name
        uploaded_file.save(source_path)

        processed_name = f"{source_path.stem}_processed{source_path.suffix}"
        processed_path = self.processed_dir / processed_name

        record = ReceiptRecord(
            filename=safe_name,
            processed_filename=processed_name,
            collection_name=collection_name,
            receipt_type=receipt_type,
        )

        try:
            PreprocessingService.preprocess_image(source_path, processed_path)
            text = self.ocr_service.extract_text(processed_path)
            parsed = ParserService.parse(text, receipt_type)

            record.merchant = parsed["merchant"]
            record.transaction_date = parsed["transaction_date"]
            record.total_amount = parsed["total_amount"]
            record.raw_ocr_text = parsed["raw_ocr_text"]
            record.status = parsed["status"]
            record.review_reasons = parsed.get("review_reasons", [])
            record.include_in_summary = record.status == "valid"
            record.updated_at = datetime.utcnow().isoformat()
        except Exception as exc:
            record.status = "broken"
            record.error_message = str(exc)
            record.review_reasons = ["processing_exception"]
            record.include_in_summary = False
            record.updated_at = datetime.utcnow().isoformat()

        StorageService.upsert_record(self.config["DATA_FILE"], record)
        return record
