"""Deterministic normalization and cleaning functions for insurance policy records."""

import re
import unicodedata
from datetime import date, datetime

_NULL_TOKENS = {"", "null", "none", "nan", "na", "n/a", "-", "--"}

_NAME_PARTICLES = {"da", "de", "do", "das", "dos", "e"}

_PRODUCT_ALIASES: dict[str, str] = {
    "AUTO": "AUTO",
    "AUTOMOVEL": "AUTO",
    "AUTOMOTIVE": "AUTO",
    "CARRO": "AUTO",
    "VEICULO": "AUTO",
    "VIDA": "VIDA",
    "LIFE": "VIDA",
    "SEGURO VIDA": "VIDA",
    "SAUDE": "SAUDE",
    "HEALTH": "SAUDE",
    "PLANO SAUDE": "SAUDE",
    "RESIDENCIAL": "RESIDENCIAL",
    "HOME": "RESIDENCIAL",
    "RESIDENCIA": "RESIDENCIAL",
    "EMPRESARIAL": "EMPRESARIAL",
    "BUSINESS": "EMPRESARIAL",
    "CORPORATIVO": "EMPRESARIAL",
}

_STATUS_ALIASES: dict[str, str] = {
    "ACTIVE": "ACTIVE",
    "ATIVO": "ACTIVE",
    "ATIVA": "ACTIVE",
    "VIGENTE": "ACTIVE",
    "PENDING": "PENDING",
    "PENDENTE": "PENDING",
    "EM ANALISE": "PENDING",
    "CANCELLED": "CANCELLED",
    "CANCELED": "CANCELLED",
    "CANCELADO": "CANCELLED",
    "CANCELADA": "CANCELLED",
    "EXPIRED": "EXPIRED",
    "EXPIRADO": "EXPIRED",
    "EXPIRADA": "EXPIRED",
    "VENCIDO": "EXPIRED",
    "VENCIDA": "EXPIRED",
}

_VALID_UFS = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
    "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
    "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}

_STATE_NAME_TO_UF: dict[str, str] = {
    "SAO PAULO": "SP",
    "RIO DE JANEIRO": "RJ",
    "MINAS GERAIS": "MG",
    "RIO GRANDE DO SUL": "RS",
    "PARANA": "PR",
    "SANTA CATARINA": "SC",
    "BAHIA": "BA",
    "PERNAMBUCO": "PE",
    "CEARA": "CE",
    "DISTRITO FEDERAL": "DF",
    "BRASILIA": "DF",
    "GOIAS": "GO",
    "ESPIRITO SANTO": "ES",
    "PARA": "PA",
    "MARANHAO": "MA",
    "AMAZONAS": "AM",
}

_EMAIL_REGEX = re.compile(r"^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$")


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _is_null_like(value: str | None) -> bool:
    if value is None:
        return True
    return str(value).strip().lower() in _NULL_TOKENS


def _is_valid_cpf(digits: str) -> bool:
    if len(digits) != 11 or len(set(digits)) == 1:
        return False
    nums = [int(d) for d in digits]
    first_sum = sum(nums[i] * (10 - i) for i in range(9))
    first_check = (first_sum * 10 % 11) % 10
    if first_check != nums[9]:
        return False
    second_sum = sum(nums[i] * (11 - i) for i in range(10))
    second_check = (second_sum * 10 % 11) % 10
    return second_check == nums[10]


def _is_valid_cnpj(digits: str) -> bool:
    if len(digits) != 14 or len(set(digits)) == 1:
        return False
    nums = [int(d) for d in digits]
    w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    w2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    r1 = sum(nums[i] * w1[i] for i in range(12)) % 11
    c1 = 0 if r1 < 2 else 11 - r1
    if c1 != nums[12]:
        return False
    r2 = sum(nums[i] * w2[i] for i in range(13)) % 11
    c2 = 0 if r2 < 2 else 11 - r2
    return c2 == nums[13]


def clean_policy_id(value: str | None) -> tuple[str | None, bool]:
    """Normalize policy identifier (trim, uppercase, replace spaces/underscores with '-')."""
    if _is_null_like(value):
        return None, False
    raw = str(value)
    cleaned = re.sub(r"[\s_]+", "-", raw.strip().upper())
    return cleaned, cleaned != raw


def clean_customer_name(value: str | None) -> tuple[str | None, bool]:
    """Normalize customer name (collapse whitespace, apply Brazilian Title Case)."""
    if _is_null_like(value):
        return None, False
    raw = str(value)
    collapsed = re.sub(r"\s+", " ", raw.strip())
    words = []
    for idx, word in enumerate(collapsed.split(" ")):
        lower = word.lower()
        if idx > 0 and lower in _NAME_PARTICLES:
            words.append(lower)
        else:
            words.append(lower.capitalize())
    cleaned = " ".join(words)
    if len(cleaned) < 2:
        return None, False
    return cleaned, cleaned != raw


def clean_document_id(value: str | None) -> tuple[str | None, bool]:
    """Strip CPF/CNPJ punctuation and validate check digits."""
    if _is_null_like(value):
        return None, False
    raw = str(value)
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 11 and _is_valid_cpf(digits):
        return digits, digits != raw
    if len(digits) == 14 and _is_valid_cnpj(digits):
        return digits, digits != raw
    return None, False


def clean_email(value: str | None) -> tuple[str | None, bool, bool]:
    """Clean optional email. Returns (cleaned_email, was_corrected, is_valid)."""
    if _is_null_like(value):
        raw = "" if value is None else str(value)
        return None, raw != "", True
    raw = str(value)
    cleaned = raw.strip().lower()
    if not _EMAIL_REGEX.match(cleaned):
        return None, False, False
    return cleaned, cleaned != raw, True


def clean_product_type(value: str | None) -> tuple[str | None, bool]:
    """Standardize insurance product line."""
    if _is_null_like(value):
        return None, False
    raw = str(value)
    normalized = _strip_accents(raw).strip().upper()
    normalized = re.sub(r"[\s_]+", " ", normalized)
    mapped = _PRODUCT_ALIASES.get(normalized)
    if not mapped:
        return None, False
    return mapped, mapped != raw


def clean_premium_amount(value: str | None) -> tuple[float | None, bool]:
    """Parse currency strings (BRL/USD formats) into a rounded float."""
    if _is_null_like(value):
        return None, False
    raw = str(value)
    s = raw.strip()
    s = re.sub(r"^[rR]\$\s*", "", s)
    s = s.replace(" ", "")

    if "," in s and "." in s:
        # Determine decimal separator by last occurrence: "1.250,50" vs "1,250.50"
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")

    try:
        parsed = round(float(s), 2)
    except ValueError:
        return None, False

    was_corrected = raw.strip() != raw or raw != f"{parsed:.2f}" and raw != str(parsed)
    return parsed, was_corrected


def clean_start_date(value: str | None) -> tuple[date | None, bool]:
    """Parse inconsistent date strings into a canonical datetime.date."""
    if _is_null_like(value):
        return None, False
    raw = str(value)
    s = raw.strip()

    # Exact ISO format requires no correction
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        try:
            return datetime.strptime(s, "%Y-%m-%d").date(), raw != s
        except ValueError:
            return None, False

    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d.%m.%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date(), True
        except ValueError:
            continue

    return None, False


def clean_status(value: str | None) -> tuple[str | None, bool]:
    """Standardize policy status."""
    if _is_null_like(value):
        return None, False
    raw = str(value)
    normalized = _strip_accents(raw).strip().upper()
    normalized = re.sub(r"[\s_]+", " ", normalized)
    mapped = _STATUS_ALIASES.get(normalized)
    if not mapped:
        return None, False
    return mapped, mapped != raw


def clean_region(value: str | None) -> tuple[str | None, bool]:
    """Standardize Brazilian state (UF) code."""
    if _is_null_like(value):
        return None, False
    raw = str(value)
    normalized = _strip_accents(raw).strip().upper()
    if normalized in _VALID_UFS:
        return normalized, normalized != raw
    mapped = _STATE_NAME_TO_UF.get(normalized)
    if mapped:
        return mapped, True
    return None, False
