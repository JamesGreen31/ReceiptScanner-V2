from __future__ import annotations

from pathlib import Path
import pytesseract
from PIL import Image


class OCRService:
    OCR_CONFIGS = [
        "--oem 3 --psm 6",
        "--oem 3 --psm 11",
        "--oem 3 --psm 4",
    ]

    def __init__(self, use_ocr: bool, ocr_log_dir: Path):
        self.use_ocr = use_ocr
        self.ocr_log_dir = ocr_log_dir

    def extract_text(self, image_path: Path) -> str:
        if not self.use_ocr:
            return "OCR disabled for this deployment."

        best_text = ""
        with Image.open(image_path) as image:
            for config in self.OCR_CONFIGS:
                candidate = pytesseract.image_to_string(image, config=config)
                if len(candidate.strip()) > len(best_text.strip()):
                    best_text = candidate
                if best_text.strip():
                    break

        log_path = self.ocr_log_dir / f"{image_path.stem}.txt"
        log_path.write_text(best_text, encoding="utf-8")
        return best_text
