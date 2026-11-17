"""FastAPI application and REST endpoints for the Insurance Data Pipeline."""

import csv
import io
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, init_db
from app.models import CleanedRecord, IngestionRun, RejectedRecord
from app.pipeline.runner import run_ingestion_pipeline
from app.schemas import (
    CleanedRecordOut,
    HealthResponse,
    IngestionReport,
    IngestionRunSummary,
    PipelineStatsResponse,
    RejectedRecordOut,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Automated ETL pipeline for cleaning, validating, deduplicating, and "
        "persisting corporate insurance policy data (CSV/XLSX) with SQL audit logs "
        "and BI-ready export endpoints."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


_BASE_DIR = Path(__file__).resolve().parent.parent
_INDEX_HTML = _BASE_DIR / "app" / "static" / "index.html"
_SAMPLE_CSV = _BASE_DIR / "data" / "sample_dirty_policies.csv"


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def web_ui() -> FileResponse:
    """Serve the accessible, non-technical Web UI."""
    return FileResponse(_INDEX_HTML)


@app.get("/api/v1/sample", tags=["Data & Export"])
def download_sample_file() -> FileResponse:
    """Download the included sample dirty CSV dataset for quick testing."""
    if not _SAMPLE_CSV.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample file not found.")
    return FileResponse(_SAMPLE_CSV, media_type="text/csv", filename="sample_dirty_policies.csv")


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check() -> HealthResponse:
    """Verify API availability."""
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
    )


@app.post(
    "/api/v1/ingest",
    response_model=IngestionReport,
    status_code=status.HTTP_201_CREATED,
    tags=["Ingestion"],
)
async def ingest_file(
    file: UploadFile = File(..., description="CSV or XLSX file containing policy records"),
    db: Session = Depends(get_db),
) -> IngestionReport:
    """Upload a CSV or Excel file, run cleaning & validation, and persist results."""
    filename = file.filename or "upload.csv"
    content = await file.read()

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.max_upload_size_mb} MB.",
        )

    try:
        run = run_ingestion_pipeline(db=db, content=content, filename=filename)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    valid_total = run.accepted_rows + run.corrected_rows
    acceptance_rate = round((valid_total / run.total_rows) * 100, 2) if run.total_rows else 0.0

    return IngestionReport(
        run_id=run.id,
        filename=run.filename,
        file_format=run.file_format,
        total_rows=run.total_rows,
        accepted_rows=run.accepted_rows,
        corrected_rows=run.corrected_rows,
        rejected_rows=run.rejected_rows,
        duplicate_rows=run.duplicate_rows,
        acceptance_rate_pct=acceptance_rate,
        processing_time_ms=run.processing_time_ms,
        status=run.status,
        created_at=run.created_at,
    )


@app.get("/api/v1/runs", response_model=list[IngestionRunSummary], tags=["Audit Logs"])
def list_ingestion_runs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[IngestionRun]:
    """List pipeline execution audit logs ordered by most recent first."""
    stmt = (
        select(IngestionRun)
        .order_by(IngestionRun.id.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


@app.get("/api/v1/runs/{run_id}", response_model=IngestionRunSummary, tags=["Audit Logs"])
def get_ingestion_run(run_id: int, db: Session = Depends(get_db)) -> IngestionRun:
    """Retrieve a specific ingestion audit log by ID."""
    run = db.get(IngestionRun, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingestion run not found.")
    return run


@app.get(
    "/api/v1/runs/{run_id}/rejected",
    response_model=list[RejectedRecordOut],
    tags=["Audit Logs"],
)
def list_rejected_records(
    run_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[RejectedRecord]:
    """Inspect rejected rows and exact validation failure reasons for a given run."""
    run = db.get(IngestionRun, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingestion run not found.")

    stmt = (
        select(RejectedRecord)
        .where(RejectedRecord.run_id == run_id)
        .order_by(RejectedRecord.row_number.asc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


@app.get("/api/v1/records", response_model=list[CleanedRecordOut], tags=["Data & Export"])
def list_cleaned_records(
    run_id: int | None = Query(None, description="Filter by ingestion run ID"),
    product_type: str | None = Query(None, description="Filter by product (AUTO, VIDA, SAUDE, RESIDENCIAL, EMPRESARIAL)"),
    record_status: str | None = Query(None, alias="status", description="Filter by status (ACTIVE, PENDING, CANCELLED, EXPIRED)"),
    region: str | None = Query(None, description="Filter by 2-letter Brazilian UF (e.g., SP, RJ)"),
    was_corrected: bool | None = Query(None, description="Filter records that were auto-corrected"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[CleanedRecord]:
    """Query cleaned and standardized records with optional analytical filters."""
    stmt = select(CleanedRecord)
    if run_id is not None:
        stmt = stmt.where(CleanedRecord.run_id == run_id)
    if product_type is not None:
        stmt = stmt.where(CleanedRecord.product_type == product_type.upper())
    if record_status is not None:
        stmt = stmt.where(CleanedRecord.status == record_status.upper())
    if region is not None:
        stmt = stmt.where(CleanedRecord.region == region.upper())
    if was_corrected is not None:
        stmt = stmt.where(CleanedRecord.was_corrected == was_corrected)

    stmt = stmt.order_by(CleanedRecord.id.asc()).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


@app.get("/api/v1/export", tags=["Data & Export"])
def export_cleaned_data(
    run_id: int | None = Query(None, description="Optional run ID to export"),
    export_format: str = Query("csv", alias="format", pattern="^(csv|json)$"),
    db: Session = Depends(get_db),
):
    """Export cleaned records as CSV or JSON for downstream BI tools (e.g., Power BI)."""
    stmt = select(CleanedRecord)
    if run_id is not None:
        stmt = stmt.where(CleanedRecord.run_id == run_id)
    stmt = stmt.order_by(CleanedRecord.id.asc())
    records = list(db.scalars(stmt).all())

    if export_format == "json":
        return [CleanedRecordOut.model_validate(r) for r in records]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "id",
            "run_id",
            "policy_id",
            "customer_name",
            "document_id",
            "email",
            "product_type",
            "premium_amount",
            "start_date",
            "status",
            "region",
            "was_corrected",
            "corrections_applied",
        ]
    )
    for r in records:
        writer.writerow(
            [
                r.id,
                r.run_id,
                r.policy_id,
                r.customer_name,
                r.document_id,
                r.email or "",
                r.product_type,
                f"{r.premium_amount:.2f}",
                r.start_date.isoformat(),
                r.status,
                r.region,
                r.was_corrected,
                r.corrections_applied or "",
            ]
        )

    output.seek(0)
    filename = f"cleaned_policies_run_{run_id}.csv" if run_id else "cleaned_policies_all.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/v1/stats", response_model=PipelineStatsResponse, tags=["System"])
def get_pipeline_stats(db: Session = Depends(get_db)) -> PipelineStatsResponse:
    """Return aggregated metrics across all pipeline executions."""
    runs_agg = db.execute(
        select(
            func.count(IngestionRun.id),
            func.coalesce(func.sum(IngestionRun.total_rows), 0),
            func.coalesce(func.avg(IngestionRun.processing_time_ms), 0.0),
        )
    ).one()

    cleaned_agg = db.execute(
        select(
            func.count(CleanedRecord.id),
            func.coalesce(func.sum(CleanedRecord.premium_amount), 0.0),
        )
    ).one()

    rejected_count = db.scalar(select(func.count(RejectedRecord.id))) or 0

    return PipelineStatsResponse(
        total_runs=int(runs_agg[0]),
        total_rows_processed=int(runs_agg[1]),
        total_cleaned_records=int(cleaned_agg[0]),
        total_rejected_records=int(rejected_count),
        avg_processing_time_ms=round(float(runs_agg[2]), 2),
        total_premium_volume=round(float(cleaned_agg[1]), 2),
    )
