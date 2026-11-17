"""Generate realistic dirty insurance policy datasets (CSV/XLSX) for testing and demos."""

import csv
import random
from pathlib import Path


def generate_valid_cpf(rng: random.Random) -> str:
    """Generate a mathematically valid 11-digit Brazilian CPF."""
    digits = [rng.randint(0, 9) for _ in range(9)]
    if len(set(digits)) == 1:
        digits[0] = (digits[0] + 1) % 10

    s1 = sum(digits[i] * (10 - i) for i in range(9))
    d1 = (s1 * 10 % 11) % 10
    digits.append(d1)

    s2 = sum(digits[i] * (11 - i) for i in range(10))
    d2 = (s2 * 10 % 11) % 10
    digits.append(d2)

    return "".join(str(d) for d in digits)


def format_cpf(digits: str) -> str:
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


def build_dirty_rows(num_rows: int = 200, seed: int = 42) -> list[dict[str, str]]:
    """Build a mix of clean, auto-correctable, duplicate, and invalid rows."""
    rng = random.Random(seed)
    first_names = ["Ana", "Bruno", "Carlos", "Daniela", "Eduardo", "Fernanda", "Gabriel", "Helena", "Lucas", "Mariana"]
    last_names = ["Silva", "Santos", "Oliveira", "Souza", "Pereira", "Costa", "Rodrigues", "Almeida"]
    products_clean = ["AUTO", "VIDA", "SAUDE", "RESIDENCIAL", "EMPRESARIAL"]
    products_dirty = ["automovel", "Saúde", "vida", "Residencial", "home", "empresarial"]
    statuses_clean = ["ACTIVE", "PENDING", "CANCELLED", "EXPIRED"]
    statuses_dirty = ["Ativo", "pendente", "Cancelado", "Vencido", "ativa"]
    regions_clean = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "DF"]
    regions_dirty = ["sp", "São Paulo", "rio de janeiro", "Minas Gerais", "rj", "mg"]

    rows: list[dict[str, str]] = []
    used_ids: list[str] = []

    for i in range(1, num_rows + 1):
        pid = f"POL-{10000 + i}"
        fname = rng.choice(first_names)
        lname = rng.choice(last_names)
        cpf = generate_valid_cpf(rng)
        email = f"{fname.lower()}.{lname.lower()}{i}@example.com"
        product = rng.choice(products_clean)
        premium = f"{rng.uniform(350.0, 8500.0):.2f}"
        year = rng.randint(2023, 2026)
        month = rng.randint(1, 12)
        day = rng.randint(1, 28)
        start_date = f"{year:04d}-{month:02d}-{day:02d}"
        status = rng.choice(statuses_clean)
        region = rng.choice(regions_clean)

        roll = rng.random()
        if roll < 0.06 and used_ids:
            # Duplicate policy_id
            pid = rng.choice(used_ids)
        elif roll < 0.12:
            # Invalid row (bad CPF, negative premium, or bad date)
            defect = rng.choice(["cpf", "premium", "date", "product"])
            if defect == "cpf":
                cpf = "111.111.111-11"
            elif defect == "premium":
                premium = "-250.00"
            elif defect == "date":
                start_date = "99/99/2025"
            else:
                product = "UNKNOWN_PLAN"
        elif roll < 0.55:
            # Dirty but auto-correctable row
            pid = f"  pol_{10000 + i} "
            fname_dirty = f"  {fname.upper()}   de  {lname.lower()} "
            cpf = format_cpf(cpf)
            email = f"  {email.upper()} "
            product = rng.choice(products_dirty)
            val = rng.uniform(350.0, 8500.0)
            premium = f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            start_date = rng.choice([f"{day:02d}/{month:02d}/{year}", f"{day:02d}-{month:02d}-{year}"])
            status = rng.choice(statuses_dirty)
            region = rng.choice(regions_dirty)
            rows.append(
                {
                    "policy_id": pid,
                    "customer_name": fname_dirty,
                    "document_id": cpf,
                    "email": email,
                    "product_type": product,
                    "premium_amount": premium,
                    "start_date": start_date,
                    "status": status,
                    "region": region,
                }
            )
            used_ids.append(f"POL-{10000 + i}")
            continue

        used_ids.append(pid)
        rows.append(
            {
                "policy_id": pid,
                "customer_name": f"{fname} {lname}",
                "document_id": cpf,
                "email": email,
                "product_type": product,
                "premium_amount": premium,
                "start_date": start_date,
                "status": status,
                "region": region,
            }
        )

    return rows


def write_sample_csv(output_path: Path, num_rows: int = 200) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = build_dirty_rows(num_rows=num_rows)
    fieldnames = list(rows[0].keys())
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    target = Path(__file__).resolve().parent.parent / "data" / "sample_dirty_policies.csv"
    write_sample_csv(target, num_rows=200)
    print(f"Generated {target} with 200 sample rows.")
