"""SQLAlchemy ORM models for ingestion audit logs, cleaned data, and rejected rows."""

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class IngestionRun(Base):
    """Audit log entry for a single pipeline execution."""

    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_format: Mapped[str] = mapped_column(String(16), nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    accepted_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    corrected_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejected_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicate_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processing_time_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    cleaned_records: Mapped[list["CleanedRecord"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    rejected_records: Mapped[list["RejectedRecord"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class CleanedRecord(Base):
    """Validated and standardized insurance policy record ready for analytics/BI."""

    __tablename__ = "cleaned_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("ingestion_runs.id", ondelete="CASCADE"), index=True)
    policy_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    customer_name: Mapped[str] = mapped_column(String(150), nullable=False)
    document_id: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    product_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    premium_amount: Mapped[float] = mapped_column(Float, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    region: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    was_corrected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    corrections_applied: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    run: Mapped["IngestionRun"] = relationship(back_populates="cleaned_records")


class RejectedRecord(Base):
    """Row rejected during validation with raw payload and failure reasons."""

    __tablename__ = "rejected_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("ingestion_runs.id", ondelete="CASCADE"), index=True)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_data: Mapped[str] = mapped_column(Text, nullable=False)
    rejection_reasons: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    run: Mapped["IngestionRun"] = relationship(back_populates="rejected_records")
