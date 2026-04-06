import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key")
    USE_OCR = os.getenv("USE_OCR", "true").lower() == "true"
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
    PROCESSED_DIR = os.getenv("PROCESSED_DIR", "processed")
    OCR_LOG_DIR = os.getenv("OCR_LOG_DIR", "ocr_logs")
    DATA_FILE = os.getenv("DATA_FILE", "instance/receipts.json")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
    RECEIPT_TYPES = ["gas", "retail", "food", "parking", "other"]
