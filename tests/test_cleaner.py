"""Unit tests for individual cleaning and normalization functions."""

from datetime import date

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


def test_clean_policy_id():
    assert clean_policy_id("POL-1001") == ("POL-1001", False)
    assert clean_policy_id("  pol_1001 ") == ("POL-1001", True)
    assert clean_policy_id("") == (None, False)


def test_clean_customer_name():
    assert clean_customer_name("Ana Silva") == ("Ana Silva", False)
    assert clean_customer_name("  JOAO   da  SILVA ") == ("Joao da Silva", True)
    assert clean_customer_name("N/A") == (None, False)


def test_clean_document_id_cpf_and_cnpj():
    # Valid CPF
    assert clean_document_id("52998224725") == ("52998224725", False)
    assert clean_document_id("529.982.247-25") == ("52998224725", True)
    # Valid CNPJ
    assert clean_document_id("11.222.333/0001-81") == ("11222333000181", True)
    # Invalid / repeated digits
    assert clean_document_id("111.111.111-11") == (None, False)
    assert clean_document_id("12345678900") == (None, False)


def test_clean_email():
    assert clean_email("ana@example.com") == ("ana@example.com", False, True)
    assert clean_email("  ANA@EXAMPLE.COM ") == ("ana@example.com", True, True)
    assert clean_email("N/A") == (None, True, True)
    assert clean_email("not-an-email") == (None, False, False)


def test_clean_product_type():
    assert clean_product_type("AUTO") == ("AUTO", False)
    assert clean_product_type("Saúde") == ("SAUDE", True)
    assert clean_product_type("automovel") == ("AUTO", True)
    assert clean_product_type("unknown") == (None, False)


def test_clean_premium_amount():
    assert clean_premium_amount("1250.50") == (1250.5, False)
    assert clean_premium_amount("R$ 1.250,50") == (1250.5, True)
    assert clean_premium_amount("1,250.50") == (1250.5, True)
    assert clean_premium_amount("1250,50") == (1250.5, True)
    assert clean_premium_amount("invalid") == (None, False)


def test_clean_start_date():
    assert clean_start_date("2026-01-15") == (date(2026, 1, 15), False)
    assert clean_start_date("15/01/2026") == (date(2026, 1, 15), True)
    assert clean_start_date("15-01-2026") == (date(2026, 1, 15), True)
    assert clean_start_date("2026/01/15") == (date(2026, 1, 15), True)
    assert clean_start_date("99/99/2026") == (None, False)


def test_clean_status():
    assert clean_status("ACTIVE") == ("ACTIVE", False)
    assert clean_status("Ativo") == ("ACTIVE", True)
    assert clean_status("Cancelada") == ("CANCELLED", True)
    assert clean_status("bogus") == (None, False)


def test_clean_region():
    assert clean_region("SP") == ("SP", False)
    assert clean_region("sp") == ("SP", True)
    assert clean_region("São Paulo") == ("SP", True)
    assert clean_region("XX") == (None, False)
