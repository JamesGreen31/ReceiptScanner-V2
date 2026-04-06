from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageChops, ImageOps


class PreprocessingService:
    @staticmethod
    def _crop_to_content(image: Image.Image, padding: int = 28) -> Image.Image:
        grayscale = ImageOps.grayscale(image)
        background = Image.new("L", grayscale.size, 255)
        diff = ImageChops.difference(background, grayscale)
        bbox = diff.getbbox()
        if not bbox:
            return image
        left, top, right, bottom = bbox
        left = max(0, left - padding)
        top = max(0, top - padding)
        right = min(image.width, right + padding)
        bottom = min(image.height, bottom + padding)
        return image.crop((left, top, right, bottom))

    @staticmethod
    def preprocess_image(input_path: Path, output_path: Path) -> Path:
        with Image.open(input_path) as image:
            cropped = PreprocessingService._crop_to_content(image)
            grayscale = ImageOps.grayscale(cropped)
            normalized = ImageOps.autocontrast(grayscale)
            width, height = normalized.size
            scaled = normalized.resize((max(width * 3, 1), max(height * 3, 1)), Image.Resampling.LANCZOS)
            thresholded = scaled.point(lambda px: 255 if px > 185 else 0)
            thresholded.save(output_path)
        return output_path
