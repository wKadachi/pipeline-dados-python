"""Pydantic v2 schemas for API request/response serialization."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    app_name: str
    version: str


class IngestionReport(BaseModel):
    """Summary returned immediately after ingesting and cleaning a file."""

    run_id: int
    filename: str
    file_format: str
    total_rows: int
    accepted_rows: int = Field(description="Rows valid as-is without auto-corrections")
    corrected_rows: int = Field(description="Rows valid after automatic cleaning/normalization")
    rejected_rows: int = Field(description="Rows rejected due to validation errors or duplicates")
    duplicate_rows: int = Field(description="Subset of rejected rows caused by duplicate policy_id")
    acceptance_rate_pct: float
    processing_time_ms: float
    status: str
    created_at: datetime


class IngestionRunSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    file_format: str
    total_rows: int
    accepted_rows: int
    corrected_rows: int
    rejected_rows: int
    duplicate_rows: int
    processing_time_ms: float
    status: str
    created_at: datetime


class CleanedRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int
    policy_id: str
    customer_name: str
    document_id: str
    email: str | None
    product_type: str
    premium_amount: float
    start_date: date
    status: str
    region: str
    was_corrected: bool
    corrections_applied: str | None
    created_at: datetime


class RejectedRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int
    row_number: int
    raw_data: str
    rejection_reasons: str
    created_at: datetime


class PipelineStatsResponse(BaseModel):
    total_runs: int
    total_rows_processed: int
    total_cleaned_records: int
    total_rejected_records: int
    avg_processing_time_ms: float
    total_premium_volume: float
