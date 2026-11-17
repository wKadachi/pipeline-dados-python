"""Unit tests for DataFrame validation, classification, and deduplication."""

import pandas as pd

from app.pipeline.validator import validate_dataframe


def test_validate_dataframe_classifies_accepted_corrected_rejected_and_duplicates():
    rows = [
        # 1. Clean row -> accepted
        {
            "policy_id": "POL-1001",
            "customer_name": "Ana Silva",
            "document_id": "52998224725",
            "email": "ana@example.com",
            "product_type": "AUTO",
            "premium_amount": "1500.00",
            "start_date": "2026-01-10",
            "status": "ACTIVE",
            "region": "SP",
        },
        # 2. Dirty but fixable -> corrected
        {
            "policy_id": "  pol_1002 ",
            "customer_name": "  BRUNO   DE  SOUZA ",
            "document_id": "529.982.247-25",
            "email": "BRUNO@EXAMPLE.COM",
            "product_type": "Saúde",
            "premium_amount": "R$ 2.350,75",
            "start_date": "15/02/2026",
            "status": "Ativo",
            "region": "São Paulo",
        },
        # 3. Duplicate policy_id -> rejected + duplicate count
        {
            "policy_id": "POL-1001",
            "customer_name": "Carlos Lima",
            "document_id": "52998224725",
            "email": "carlos@example.com",
            "product_type": "VIDA",
            "premium_amount": "900.00",
            "start_date": "2026-03-01",
            "status": "ACTIVE",
            "region": "RJ",
        },
        # 4. Invalid CPF & negative premium -> rejected
        {
            "policy_id": "POL-1004",
            "customer_name": "Daniela Costa",
            "document_id": "111.111.111-11",
            "email": "bad-email",
            "product_type": "AUTO",
            "premium_amount": "-100.00",
            "start_date": "2026-03-01",
            "status": "ACTIVE",
            "region": "MG",
        },
    ]

    df = pd.DataFrame(rows, dtype=str)
    result = validate_dataframe(df)

    assert result.total_rows == 4
    assert result.accepted_rows == 1
    assert result.corrected_rows == 1
    assert result.rejected_rows == 2
    assert result.duplicate_rows == 1
    assert len(result.cleaned_records) == 2
    assert len(result.rejected_records) == 2

    corrected_rec = result.cleaned_records[1]
    assert corrected_rec["policy_id"] == "POL-1002"
    assert corrected_rec["customer_name"] == "Bruno de Souza"
    assert corrected_rec["premium_amount"] == 2350.75
    assert corrected_rec["was_corrected"] is True
    assert "premium_amount:currency_parsed" in corrected_rec["corrections_applied"]

    assert "duplicate_policy_id" in result.rejected_records[0]["rejection_reasons"]
    assert "invalid_document_id" in result.rejected_records[1]["rejection_reasons"]
    assert "non_positive_premium" in result.rejected_records[1]["rejection_reasons"]
