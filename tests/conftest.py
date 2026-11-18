import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(scope="session")
def data():
    from forecastiq.data import generate
    return generate()


@pytest.fixture(scope="session")
def client():
    from app import app
    return app.test_client()
