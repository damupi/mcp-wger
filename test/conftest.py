import pytest


@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WGER_BASE_URL", "http://testserver/api/v2")
    monkeypatch.setenv("WGER_API_TOKEN", "test-token-12345")
