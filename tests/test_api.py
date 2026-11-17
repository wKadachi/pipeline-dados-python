"""Integration tests for FastAPI endpoints."""

import io

import pandas as pd


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_web_ui_and_sample_endpoint(client):
    ui_resp = client.get("/")
    assert ui_resp.status_code == 200
    assert "Pipeline de Limpeza" in ui_resp.text

    sample_resp = client.get("/api/v1/sample")
    assert sample_resp.status_code == 200
    assert "policy_id" in sample_resp.text


def test_ingest_csv_and_query_endpoints(client):
    csv_content = (
        "policy_id;customer_name;document_id;email;product_type;premium_amount;start_date;status;region\n"
        "POL-2001;Ana Silva;52998224725;ana@example.com;AUTO;1200.00;2026-01-05;ACTIVE;SP\n"
        "pol_2002;  JOAO  PEREIRA ;529.982.247-25;JOAO@EXAMPLE.COM;Saúde;R$ 1.850,50;10/02/2026;Ativo;rio de janeiro\n"
        "POL-2001;Duplicate Row;52998224725;dup@example.com;VIDA;500.00;2026-01-05;ACTIVE;MG\n"
        "POL-2004;Bad Row;00000000000;bad;UNKNOWN;-50;invalid;ACTIVE;XX\n"
    ).encode("utf-8")

    ingest_resp = client.post(
        "/api/v1/ingest",
        files={"file": ("policies.csv", csv_content, "text/csv")},
    )
    assert ingest_resp.status_code == 201
    report = ingest_resp.json()
    assert report["total_rows"] == 4
    assert report["accepted_rows"] == 1
    assert report["corrected_rows"] == 1
    assert report["rejected_rows"] == 2
    assert report["duplicate_rows"] == 1
    assert report["acceptance_rate_pct"] == 50.0
    run_id = report["run_id"]

    # Check audit runs
    runs_resp = client.get("/api/v1/runs")
    assert runs_resp.status_code == 200
    assert len(runs_resp.json()) == 1

    # Check single run
    run_resp = client.get(f"/api/v1/runs/{run_id}")
    assert run_resp.status_code == 200
    assert run_resp.json()["filename"] == "policies.csv"

    # Check rejected records
    rej_resp = client.get(f"/api/v1/runs/{run_id}/rejected")
    assert rej_resp.status_code == 200
    rejected = rej_resp.json()
    assert len(rejected) == 2
    assert rejected[0]["row_number"] == 3

    # Check filtered cleaned records
    rec_resp = client.get("/api/v1/records", params={"region": "RJ", "was_corrected": "true"})
    assert rec_resp.status_code == 200
    records = rec_resp.json()
    assert len(records) == 1
    assert records[0]["policy_id"] == "POL-2002"
    assert records[0]["premium_amount"] == 1850.5

    # Check CSV export
    export_csv = client.get("/api/v1/export", params={"format": "csv", "run_id": run_id})
    assert export_csv.status_code == 200
    assert "text/csv" in export_csv.headers["content-type"]
    assert "POL-2001" in export_csv.text
    assert "POL-2002" in export_csv.text

    # Check JSON export
    export_json = client.get("/api/v1/export", params={"format": "json"})
    assert export_json.status_code == 200
    assert len(export_json.json()) == 2

    # Check stats
    stats_resp = client.get("/api/v1/stats")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["total_runs"] == 1
    assert stats["total_cleaned_records"] == 2
    assert stats["total_rejected_records"] == 2
    assert stats["total_premium_volume"] == 3050.5


def test_ingest_xlsx_file(client):
    df = pd.DataFrame(
        [
            {
                "apolice": "POL-3001",
                "nome_cliente": "Mariana Costa",
                "cpf": "52998224725",
                "email": "mariana@example.com",
                "produto": "VIDA",
                "premio": "750.00",
                "data_inicio": "2026-04-01",
                "situacao": "Ativa",
                "uf": "MG",
            }
        ]
    )
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)

    resp = client.post(
        "/api/v1/ingest",
        files={"file": ("policies.xlsx", buf.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["file_format"] == "xlsx"
    assert data["corrected_rows"] == 1


def test_ingest_unsupported_format_returns_400(client):
    resp = client.post(
        "/api/v1/ingest",
        files={"file": ("notes.txt", b"hello world", "text/plain")},
    )
    assert resp.status_code == 400
    assert "Unsupported file format" in resp.json()["detail"]
