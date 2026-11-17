"""Pytest fixtures for isolated database and FastAPI TestClient testing."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.database import create_db_engine, get_db, init_db
from app.main import app


@pytest.fixture()
def client(tmp_path):
    """Provide a FastAPI TestClient backed by a fresh temporary SQLite database."""
    db_file = tmp_path / "test_pipeline.db"
    test_engine = create_db_engine(f"sqlite:///{db_file}")
    init_db(test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine, future=True)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    test_engine.dispose()
