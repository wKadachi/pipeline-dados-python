"""Benchmark script measuring end-to-end ingestion, cleaning, validation, and SQLite persistence."""

import csv
import io
import sys
import tempfile
import time
from pathlib import Path

from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import create_db_engine, init_db
from app.pipeline.runner import run_ingestion_pipeline
from scripts.generate_sample_data import build_dirty_rows


def _rows_to_csv_bytes(rows: list[dict[str, str]]) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def run_benchmark(sizes: list[int] | None = None) -> None:
    sizes = sizes or [1_000, 10_000, 50_000]
    print("=" * 72)
    print("Insurance Data Pipeline — Performance Benchmark (End-to-End + SQLite)")
    print("=" * 72)

    with tempfile.TemporaryDirectory() as tmpdir:
        for count in sizes:
            rows = build_dirty_rows(num_rows=count, seed=42)
            payload = _rows_to_csv_bytes(rows)

            db_path = Path(tmpdir) / f"bench_{count}.db"
            engine = create_db_engine(f"sqlite:///{db_path}")
            init_db(engine)
            Session = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

            with Session() as db:
                t0 = time.perf_counter()
                run = run_ingestion_pipeline(db=db, content=payload, filename=f"bench_{count}.csv")
                total_sec = time.perf_counter() - t0

            throughput = round(count / total_sec) if total_sec > 0 else 0
            print(
                f"Rows: {count:>6,} | Time: {total_sec:>6.3f}s ({run.processing_time_ms:>8.2f} ms) | "
                f"Throughput: {throughput:>7,} rows/s | "
                f"Accepted: {run.accepted_rows:,}, Corrected: {run.corrected_rows:,}, Rejected: {run.rejected_rows:,}"
            )
            engine.dispose()


if __name__ == "__main__":
    run_benchmark()
