import importlib.util
from pathlib import Path


def _load_fxmacrodata_module():
    path = Path(__file__).parents[1] / "fastquant" / "data" / "fxmacrodata.py"
    spec = importlib.util.spec_from_file_location("fastquant_fxmacrodata", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_get_fxmacrodata_data(monkeypatch):
    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "data": [
                    {"date": "2026-01-02", "val": 1.2},
                    {"date": "2026-01-01", "val": 1.1},
                ]
            }

    calls = {}

    def mock_get(url, params, headers, timeout):
        calls["url"] = url
        calls["params"] = params
        calls["headers"] = headers
        calls["timeout"] = timeout
        return MockResponse()

    fxmacrodata = _load_fxmacrodata_module()
    monkeypatch.setattr(fxmacrodata.requests, "get", mock_get)
    df = fxmacrodata.get_fxmacrodata_data(
        "EUR/USD",
        "2026-01-01",
        "2026-01-02",
        api_key="test-key",
        api_root="https://example.test/api/v1",
    )

    assert calls["url"] == "https://example.test/api/v1/forex/EUR/USD"
    assert calls["params"]["start_date"] == "2026-01-01"
    assert calls["headers"] == {"X-API-Key": "test-key"}
    assert list(df["close"]) == [1.1, 1.2]
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
