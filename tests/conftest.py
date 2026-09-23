import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def client(tmp_path):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'smoke.db'}", test_mode=False)
    with TestClient(create_app(settings)) as client:
        yield client
