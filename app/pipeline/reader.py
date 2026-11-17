"""File reader for CSV and Excel spreadsheets with encoding/delimiter auto-detection."""

import csv
import io
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {
    "policy_id",
    "customer_name",
    "document_id",
    "product_type",
    "premium_amount",
    "start_date",
    "status",
    "region",
}

COLUMN_ALIASES: dict[str, str] = {
    "apolice": "policy_id",
    "id_apolice": "policy_id",
    "numero_apolice": "policy_id",
    "policy": "policy_id",
    "policy_number": "policy_id",
    "nome": "customer_name",
    "nome_cliente": "customer_name",
    "cliente": "customer_name",
    "segurado": "customer_name",
    "cpf": "document_id",
    "cnpj": "document_id",
    "cpf_cnpj": "document_id",
    "documento": "document_id",
    "e_mail": "email",
    "produto": "product_type",
    "tipo_produto": "product_type",
    "ramo": "product_type",
    "premio": "premium_amount",
    "valor_premio": "premium_amount",
    "valor": "premium_amount",
    "premium": "premium_amount",
    "data_inicio": "start_date",
    "inicio_vigencia": "start_date",
    "vigencia": "start_date",
    "situacao": "status",
    "uf": "region",
    "estado": "region",
    "regiao": "region",
}


def _normalize_column_name(col: str) -> str:
    cleaned = str(col).strip().lower().replace(" ", "_").replace("-", "_")
    return COLUMN_ALIASES.get(cleaned, cleaned)


def _decode_csv_bytes(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def _detect_delimiter(sample_text: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(sample_text[:4096], delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        first_line = sample_text.splitlines()[0] if sample_text else ""
        if first_line.count(";") > first_line.count(","):
            return ";"
        return ","


def read_tabular_bytes(content: bytes, filename: str) -> tuple[pd.DataFrame, str]:
    """Read raw CSV or XLSX bytes into a string-typed DataFrame with normalized headers.

    Returns:
        Tuple of (DataFrame, detected_format) where detected_format is 'csv' or 'xlsx'.
    """
    if not content:
        raise ValueError("Uploaded file is empty.")

    ext = Path(filename).suffix.lower()

    if ext == ".csv":
        text = _decode_csv_bytes(content)
        delimiter = _detect_delimiter(text)
        df = pd.read_csv(
            io.StringIO(text),
            sep=delimiter,
            dtype=str,
            keep_default_na=False,
        )
        file_format = "csv"
    elif ext in {".xlsx", ".xls"}:
        df = pd.read_excel(
            io.BytesIO(content),
            dtype=str,
            keep_default_na=False,
        )
        file_format = "xlsx"
    else:
        raise ValueError(f"Unsupported file format '{ext}'. Supported formats: .csv, .xlsx")

    df.columns = [_normalize_column_name(c) for c in df.columns]

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    if "email" not in df.columns:
        df["email"] = ""

    return df, file_format
