"""Pipeline runner orchestrating file ingestion, validation, timing, and SQL persistence."""

import time

from sqlalchemy.orm import Session

from app.models import CleanedRecord, IngestionRun, RejectedRecord
from app.pipeline.reader import read_tabular_bytes
from app.pipeline.validator import validate_dataframe


def run_ingestion_pipeline(
    db: Session,
    content: bytes,
    filename: str,
) -> IngestionRun:
    """Execute full ETL pipeline on uploaded file bytes and persist results + audit log."""
    start_time = time.perf_counter()

    df, file_format = read_tabular_bytes(content, filename)
    validation = validate_dataframe(df)

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

    run = IngestionRun(
        filename=filename,
        file_format=file_format,
        total_rows=validation.total_rows,
        accepted_rows=validation.accepted_rows,
        corrected_rows=validation.corrected_rows,
        rejected_rows=validation.rejected_rows,
        duplicate_rows=validation.duplicate_rows,
        processing_time_ms=elapsed_ms,
        status="completed",
    )
    db.add(run)
    db.flush()  # Populate run.id before bulk inserting child rows

    if validation.cleaned_records:
        cleaned_objs = [
            CleanedRecord(run_id=run.id, **rec) for rec in validation.cleaned_records
        ]
        db.bulk_save_objects(cleaned_objs)

    if validation.rejected_records:
        rejected_objs = [
            RejectedRecord(run_id=run.id, **rec) for rec in validation.rejected_records
        ]
        db.bulk_save_objects(rejected_objs)

    db.commit()
    db.refresh(run)
    return run
