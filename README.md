# Insurance Data Cleaning, Validation & Automation Pipeline

Automated Python ETL pipeline and REST API built with **FastAPI**, **Pandas**, **Pydantic**, and **SQLAlchemy**. Designed to replace hours of manual spreadsheet cleanup with deterministic, auditable, sub-second data processing.

> **Portfolio Context:** Built by **Luis Henriques Figueiredo** (Backend / Full Stack & Data Automation Developer), translating real-world insurance operations experience at Bradesco Seguros into a production-ready Python service.

---

## Key Features

- **Multi-Format Ingestion (`.csv` & `.xlsx`):** Auto-detects CSV encodings (`UTF-8`, `UTF-8-SIG`, `Latin-1`) and delimiters (`,`, `;`, `\t`, `|`), plus bilingual column header mapping (English & Portuguese aliases).
- **Deterministic Cleaning & Normalization Engine:**
  - **Policy IDs:** Trims whitespace, uppercases, and standardizes separators (`" pol_1001 "` → `"POL-1001"`).
  - **Customer Names:** Collapses extra whitespace and applies Brazilian Title Case (`"  JOAO   da  SILVA "` → `"Joao da Silva"`).
  - **CPF / CNPJ Validation:** Strips punctuation and verifies official Brazilian check digits (11-digit CPF / 14-digit CNPJ).
  - **Currency Parsing:** Normalizes BRL (`R$ 1.250,50`) and US (`1,250.50`) formats into rounded floats.
  - **Date Standardization:** Converts inconsistent formats (`DD/MM/YYYY`, `DD-MM-YYYY`, `YYYY/MM/DD`) into canonical ISO-8601 (`YYYY-MM-DD`).
  - **Domain Enums & UFs:** Maps Portuguese/English product lines (`Saúde` → `SAUDE`), statuses (`Ativo` → `ACTIVE`), and state names (`São Paulo` → `SP`).
- **Row-Level Classification & Audit Trail:**
  - Every row is classified as **Accepted** (valid as-is), **Corrected** (valid after logged auto-fixes), or **Rejected** (with exact failure reasons and raw payload stored for auditing).
  - Automatic intra-batch deduplication by `policy_id`.
- **SQL Persistence & BI Export:**
  - Persists cleaned records, rejected rows, and execution audit logs in **SQLite** (default) or **PostgreSQL** via `DATABASE_URL`.
  - Provides `/api/v1/export` (`csv` or `json`) ready for downstream **Power BI** dashboards.

---

## Tech Stack

- **Language:** Python 3.12
- **API & Validation:** FastAPI, Uvicorn, Pydantic v2
- **Data Processing:** Pandas, OpenPyXL
- **Database & ORM:** SQLAlchemy 2.0 (SQLite / PostgreSQL)
- **Testing:** Pytest + FastAPI `TestClient`
- **Packaging:** Docker

---

## Project Structure

```text
pipeline-dados-python/
├── app/
│   ├── main.py              # FastAPI app & REST endpoints (/docs)
│   ├── config.py            # Environment-based settings
│   ├── database.py          # SQLAlchemy engine & session management
│   ├── models.py            # ORM models (IngestionRun, CleanedRecord, RejectedRecord)
│   ├── schemas.py           # Pydantic v2 response schemas
│   └── pipeline/
│       ├── reader.py        # CSV/XLSX reader with encoding & delimiter detection
│       ├── cleaner.py       # Deterministic field normalization & CPF/CNPJ check digits
│       ├── validator.py     # Row-level validation, deduplication & classification
│       └── runner.py        # Orchestrator + timing & bulk SQL persistence
├── data/
│   └── sample_dirty_policies.csv
├── scripts/
│   ├── generate_sample_data.py
│   └── benchmark.py
├── tests/
│   ├── conftest.py
│   ├── test_cleaner.py
│   ├── test_validator.py
│   └── test_api.py
├── Dockerfile
└── requirements.txt
```

---

## Performance Benchmark

Measured end-to-end (CSV parsing + regex/check-digit validation + deduplication + SQLite bulk persistence) using `scripts/benchmark.py` on Windows (Python 3.12):

| Dataset Size | Total Time | Pipeline Time | Throughput |
| ---: | ---: | ---: | ---: |
| 1,000 rows | 0.117 s | 55.24 ms | 8,556 rows/s |
| 10,000 rows | 0.905 s | 415.50 ms | 11,048 rows/s |
| 50,000 rows | 4.452 s | 1,964.83 ms | 11,232 rows/s |

Run the benchmark yourself:

```bash
python scripts/benchmark.py
```

---

## Quick Start (Local)

1. **Create and activate a virtual environment:**

   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   # Linux/macOS:
   source .venv/bin/activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the API server:**

   ```bash
   uvicorn app.main:app --reload
   ```

4. **Open interactive Swagger docs:**
   - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
   - ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

5. **Test with the included sample dataset:**

   ```bash
   curl -X POST "http://localhost:8000/api/v1/ingest" \
     -F "file=@data/sample_dirty_policies.csv"
   ```

---

## Running with Docker

```bash
docker build -t insurance-data-pipeline .
docker run -p 8000:8000 insurance-data-pipeline
```

To connect to PostgreSQL instead of SQLite:

```bash
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql+psycopg2://user:password@host:5432/pipeline_db" \
  insurance-data-pipeline
```

---

## API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health check |
| `POST` | `/api/v1/ingest` | Upload `.csv` or `.xlsx` file, clean/validate, and persist |
| `GET` | `/api/v1/runs` | List pipeline execution audit logs |
| `GET` | `/api/v1/runs/{run_id}` | Get details for a specific ingestion run |
| `GET` | `/api/v1/runs/{run_id}/rejected` | Inspect rejected rows, raw payloads, and failure reasons |
| `GET` | `/api/v1/records` | Query cleaned records (filter by `product_type`, `status`, `region`, `was_corrected`) |
| `GET` | `/api/v1/export` | Export cleaned dataset as `csv` or `json` (Power BI ready) |
| `GET` | `/api/v1/stats` | Aggregated metrics across all runs |

---

## Running Tests

```bash
pytest -v
```
