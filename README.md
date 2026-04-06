# Receipt Scanner V2 - Flask Implementation

Flask implementation scaffold for James Green, Marymount University, package namespace `marymount.edu`, for IT568A.

## Notable behavior in this revision

- Supports named **collections** for grouping receipts.
- Collection search filters both the **receipt list** and the **monthly summary**.
- Category chips filter and sort the receipt list by the selected receipt type.
- Receipts with missing required fields are marked `needs_review`, highlighted yellow in the UI, and excluded from summary calculations.
- Merchant identification is retained as a helpful parsed field but is **not required** for a receipt to become `valid`.

## Run locally with Docker

```bash
docker compose up --build
```

Open:

```text
http://127.0.0.1:5000
```

## Project notes

- OCR runs through `pytesseract` with `tesseract-ocr` installed in the container.
- Receipt data is persisted in `instance/receipts.json`.
- Uploaded files go to `uploads/`, processed images to `processed/`, and OCR logs to `ocr_logs/`.


Recent UI/behavior updates
- Added CKPlace.org green logo styling and a polished non-wireframe visual theme.
- Added Delete action for individual receipts.
- Added Reset All to wipe the receipt store.
- Reset View now only clears active view filters.
- OCR total extraction now always selects the highest recognized dollar figure.
