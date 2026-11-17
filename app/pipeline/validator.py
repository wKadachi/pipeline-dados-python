"""Row-level validation, deduplication, and classification engine."""

import json
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from app.pipeline.cleaner import (
    clean_customer_name,
    clean_document_id,
    clean_email,
    clean_policy_id,
    clean_premium_amount,
    clean_product_type,
    clean_region,
    clean_start_date,
    clean_status,
)


@dataclass
class ValidationResult:
    """Aggregated output of validating and cleaning a tabular dataset."""

    total_rows: int = 0
    accepted_rows: int = 0
    corrected_rows: int = 0
    rejected_rows: int = 0
    duplicate_rows: int = 0
    cleaned_records: list[dict[str, Any]] = field(default_factory=list)
    rejected_records: list[dict[str, Any]] = field(default_factory=list)


def validate_dataframe(df: pd.DataFrame) -> ValidationResult:
    """Clean, deduplicate, and validate every row in a DataFrame."""
    result = ValidationResult(total_rows=len(df))
    seen_policy_ids: set[str] = set()

    for idx, row in enumerate(df.to_dict(orient="records"), start=1):
        errors: list[str] = []
        corrections: list[str] = []

        policy_id, pol_corr = clean_policy_id(row.get("policy_id"))
        if policy_id is None:
            errors.append("missing_or_invalid_policy_id")
        else:
            if policy_id in seen_policy_ids:
                errors.append("duplicate_policy_id")
            if pol_corr:
                corrections.append("policy_id:normalized")

        customer_name, name_corr = clean_customer_name(row.get("customer_name"))
        if customer_name is None:
            errors.append("missing_or_invalid_customer_name")
        elif name_corr:
            corrections.append("customer_name:title_case")

        document_id, doc_corr = clean_document_id(row.get("document_id"))
        if document_id is None:
            errors.append("invalid_document_id")
        elif doc_corr:
            corrections.append("document_id:digits_only")

        email, email_corr, email_valid = clean_email(row.get("email"))
        if not email_valid:
            errors.append("invalid_email")
        elif email_corr:
            corrections.append("email:normalized")

        product_type, prod_corr = clean_product_type(row.get("product_type"))
        if product_type is None:
            errors.append("invalid_product_type")
        elif prod_corr:
            corrections.append("product_type:standardized")

        premium_amount, prem_corr = clean_premium_amount(row.get("premium_amount"))
        if premium_amount is None:
            errors.append("invalid_premium_amount")
        elif premium_amount <= 0:
            errors.append("non_positive_premium")
        elif prem_corr:
            corrections.append("premium_amount:currency_parsed")

        start_date, date_corr = clean_start_date(row.get("start_date"))
        if start_date is None:
            errors.append("invalid_start_date")
        elif date_corr:
            corrections.append("start_date:iso_standardized")

        status, status_corr = clean_status(row.get("status"))
        if status is None:
            errors.append("invalid_status")
        elif status_corr:
            corrections.append("status:standardized")

        region, reg_corr = clean_region(row.get("region"))
        if region is None:
            errors.append("invalid_region")
        elif reg_corr:
            corrections.append("region:uf_standardized")

        if errors:
            result.rejected_rows += 1
            if "duplicate_policy_id" in errors:
                result.duplicate_rows += 1
            result.rejected_records.append(
                {
                    "row_number": idx,
                    "raw_data": json.dumps(row, ensure_ascii=False),
                    "rejection_reasons": ";".join(errors),
                }
            )
            continue

        seen_policy_ids.add(policy_id)  # type: ignore[arg-type]
        was_corrected = len(corrections) > 0
        if was_corrected:
            result.corrected_rows += 1
        else:
            result.accepted_rows += 1

        result.cleaned_records.append(
            {
                "policy_id": policy_id,
                "customer_name": customer_name,
                "document_id": document_id,
                "email": email,
                "product_type": product_type,
                "premium_amount": premium_amount,
                "start_date": start_date,
                "status": status,
                "region": region,
                "was_corrected": was_corrected,
                "corrections_applied": ";".join(corrections) if corrections else None,
            }
        )

    return result
