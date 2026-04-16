from __future__ import annotations

from datetime import datetime
from flask import (
    Blueprint,
    Response,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename
from pathlib import Path

from ..services.export_service import ExportService
from ..services.receipt_pipeline import ReceiptPipeline
from ..services.storage_service import StorageService
from ..services.summary_service import SummaryService

receipts_bp = Blueprint("receipts", __name__)


def _filtered_records(all_records):
    active_collection = request.args.get("collection") or "Default"
    search_query = request.args.get("q", "").strip()
    active_category = request.args.get("category") or "all"
    active_month = request.args.get("month") or "all"
    active_year = request.args.get("year") or "all"

    records = StorageService.filter_records(
        all_records,
        collection_name=active_collection,
        category=active_category,
        query=search_query,
    )

    if active_month != "all":
        records = [r for r in records if r.transaction_date and r.transaction_date.startswith(active_month)]
    if active_year != "all":
        records = [r for r in records if r.transaction_date and r.transaction_date[:4] == active_year]

    records = sorted(records, key=lambda r: (r.receipt_type, r.transaction_date or "", r.filename.lower()))
    return active_collection, search_query, active_category, active_month, active_year, records


@receipts_bp.get("/")
def index():
    all_records = StorageService.load_records(current_app.config["DATA_FILE"])
    active_collection, search_query, active_category, active_month, active_year, records = _filtered_records(all_records)
    summaries = SummaryService.monthly_summary(records)
    sidebar = SummaryService.sidebar_metrics(records)
    collections = StorageService.collection_names(current_app.config["DATA_FILE"])

    category_counts = {receipt_type: 0 for receipt_type in current_app.config["RECEIPT_TYPES"]}
    collection_scoped = StorageService.filter_records(all_records, collection_name=active_collection, query=search_query)
    for record in collection_scoped:
        category_counts[record.receipt_type] = category_counts.get(record.receipt_type, 0) + 1

    month_options = SummaryService.available_months(StorageService.filter_records(all_records, collection_name=active_collection, query=search_query))
    year_options = SummaryService.available_years(StorageService.filter_records(all_records, collection_name=active_collection, query=search_query))

    selected_category_label = "All" if active_category == "all" else active_category.capitalize()

    return render_template(
        "index.html",
        records=records,
        summaries=summaries,
        sidebar=sidebar,
        collections=collections,
        active_collection=active_collection,
        active_category=active_category,
        active_month=active_month,
        active_year=active_year,
        search_query=search_query,
        category_counts=category_counts,
        receipt_types=current_app.config["RECEIPT_TYPES"],
        month_options=month_options,
        year_options=year_options,
        selected_category_label=selected_category_label,
    )


@receipts_bp.get("/reset-view")
def reset_view():
    return redirect(url_for("receipts.index"))


@receipts_bp.post("/reset-all")
def reset_all():
    StorageService.clear_all(current_app.config["DATA_FILE"])
    flash("All receipts were removed from the store.", "warning")
    return redirect(url_for("receipts.index"))


@receipts_bp.get("/clear-filters")
def clear_filters():
    active_collection = request.args.get("collection") or "Default"
    return redirect(url_for("receipts.index", collection=active_collection))


@receipts_bp.post("/upload")
def upload_receipts():
    files = request.files.getlist("receipts")
    receipt_type = request.form.get("receipt_type", "other")
    collection_name = (request.form.get("collection_name") or "Default").strip() or "Default"
    pipeline = ReceiptPipeline(current_app.config)

    for uploaded_file in files:
        record = pipeline.process_upload(uploaded_file, receipt_type, collection_name)
        if record.status == "broken":
            flash(f"{record.filename or 'Receipt'} failed: {record.error_message or 'processing error'}", "error")
        elif record.status == "needs_review":
            flash(f"Processed {record.filename}. Review required before it is included in summaries.", "warning")
        else:
            flash(f"Processed {record.filename} and added it to collection {record.collection_name}.", "success")

    return redirect(url_for("receipts.index", collection=collection_name))


@receipts_bp.get("/receipts/<receipt_id>/edit")
def edit_receipt(receipt_id: str):
    record = StorageService.get_record(current_app.config["DATA_FILE"], receipt_id)
    if record is None:
        return render_template("errors/404.html"), 404
    return render_template("receipts/edit.html", record=record, receipt_types=current_app.config["RECEIPT_TYPES"])


@receipts_bp.post("/receipts/<receipt_id>/edit")
def update_receipt(receipt_id: str):
    record = StorageService.get_record(current_app.config["DATA_FILE"], receipt_id)
    if record is None:
        return render_template("errors/404.html"), 404

    record.collection_name = (request.form.get("collection_name") or record.collection_name).strip() or "Default"
    record.merchant = request.form.get("merchant") or None
    record.transaction_date = request.form.get("transaction_date") or None
    total_amount = request.form.get("total_amount", "").strip()
    record.total_amount = float(total_amount) if total_amount else None
    record.receipt_type = request.form.get("receipt_type", record.receipt_type)
    review_reasons = []
    if not record.transaction_date:
        review_reasons.append("missing_date")
    if record.total_amount is None:
        review_reasons.append("missing_total")
    record.review_reasons = review_reasons

    if request.form.get("status") == "broken":
        record.status = "broken"
        record.include_in_summary = False
    else:
        record.status = "valid" if not record.review_reasons else "needs_review"
        allow_summary = request.form.get("include_in_summary") == "on"
        record.include_in_summary = allow_summary and record.status == "valid"

    record.updated_at = datetime.utcnow().isoformat()

    StorageService.upsert_record(current_app.config["DATA_FILE"], record)
    flash(f"Updated {record.filename}", "success")
    return redirect(url_for("receipts.index", collection=record.collection_name))


@receipts_bp.post("/receipts/<receipt_id>/toggle-summary")
def toggle_summary(receipt_id: str):
    record = StorageService.get_record(current_app.config["DATA_FILE"], receipt_id)
    if record is None:
        return render_template("errors/404.html"), 404
    if record.status == "valid":
        record.include_in_summary = not record.include_in_summary
        flash(f"Summary inclusion updated for {record.filename}", "success")
    else:
        record.include_in_summary = False
        flash("Only valid receipts can be included in summaries.", "warning")
    record.updated_at = datetime.utcnow().isoformat()
    StorageService.upsert_record(current_app.config["DATA_FILE"], record)
    return redirect(url_for("receipts.index", collection=record.collection_name))


@receipts_bp.post("/receipts/<receipt_id>/delete")
def delete_receipt(receipt_id: str):
    deleted = StorageService.delete_record(current_app.config["DATA_FILE"], receipt_id)
    if deleted is None:
        return render_template("errors/404.html"), 404
    flash(f"Deleted {deleted.filename}", "warning")
    return redirect(url_for("receipts.index", collection=deleted.collection_name))


@receipts_bp.get("/export.csv")
def export_csv():
    all_records = StorageService.load_records(current_app.config["DATA_FILE"])
    _, _, _, _, _, records = _filtered_records(all_records)
    csv_data = ExportService.to_csv(records)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=receipt_scanner_export.csv"},
    )

@receipts_bp.get("/receipts/<receipt_id>/image/original")
def receipt_original_image(receipt_id: str):
    record = StorageService.get_record(current_app.config["DATA_FILE"], receipt_id)
    if record is None or not record.filename:
        return render_template("errors/404.html"), 404

    upload_dir = Path(current_app.config["UPLOAD_DIR"]).resolve()
    return send_from_directory(upload_dir, secure_filename(record.filename))

@receipts_bp.get("/receipts/<receipt_id>/image/processed")
def receipt_processed_image(receipt_id: str):
    record = StorageService.get_record(current_app.config["DATA_FILE"], receipt_id)
    if record is None or not record.processed_filename:
        return render_template("errors/404.html"), 404

    processed_dir = Path(current_app.config["PROCESSED_DIR"]).resolve()
    return send_from_directory(processed_dir, secure_filename(record.processed_filename))

@receipts_bp.post("/receipts/delete-selected")
def delete_selected():
    selected_ids = request.form.get("selected_ids", "").strip()
    active_collection = request.form.get("collection") or "Default"

    if not selected_ids:
        flash("No receipts were selected.", "warning")
        return redirect(url_for("receipts.index", collection=active_collection))

    deleted_count = 0
    for receipt_id in [rid for rid in selected_ids.split(",") if rid.strip()]:
        deleted = StorageService.delete_record(current_app.config["DATA_FILE"], receipt_id.strip())
        if deleted is not None:
            deleted_count += 1

    flash(f"Deleted {deleted_count} selected receipt(s).", "warning")
    return redirect(url_for("receipts.index", collection=active_collection))