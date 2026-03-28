from fastapi import FastAPI

from pharma_os.main import create_application


def test_application_factory_returns_fastapi() -> None:
    app = create_application()
    assert isinstance(app, FastAPI)
