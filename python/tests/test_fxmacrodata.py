import importlib.util
from pathlib import Path
import pytest
from unittest.mock import Mock


def _boundary_response(payload, status=200):
    response = Mock()
    response.status_code = status
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_redirects_are_blocked_before_body_parse(monkeypatch):
    module = _load_fxmacrodata_module()
    response = _boundary_response({"data": []}, 302)
    get = Mock(return_value=response)
    monkeypatch.setattr(module.requests, "get", get)
    with pytest.raises(module.requests.HTTPError):
        module.get_fxmacrodata_data("EURUSD", "2026-01-01", "2026-01-04", api_key="fixture-key")
    assert get.call_args.kwargs["allow_redirects"] is False
    response.json.assert_not_called()


@pytest.mark.parametrize("payload", [{"detail": "fixture-private-value"}, {"error": "fixture-private-value"}, {}, None])
def test_malformed_page_is_not_an_empty_success(monkeypatch, payload):
    module = _load_fxmacrodata_module()
    monkeypatch.setattr(module.requests, "get", Mock(return_value=_boundary_response(payload)))
    with pytest.raises(ValueError) as raised:
        module.get_fxmacrodata_data("EURUSD", "2026-01-01", "2026-01-04")
    assert "fixture-private-value" not in str(raised.value)


def test_bad_key_is_rejected_before_transport(monkeypatch):
    module = _load_fxmacrodata_module()
    get = Mock()
    monkeypatch.setattr(module.requests, "get", get)
    with pytest.raises(ValueError) as raised:
        module.get_fxmacrodata_data("EURUSD", "2026-01-01", "2026-01-04", api_key="fixture-key\r\nX-Other: value")
    assert "fixture-key" not in str(raised.value)
    get.assert_not_called()


@pytest.mark.parametrize("next_offset", [0, -1, "bad", True, 1.5])
def test_nonadvancing_pagination_is_rejected(monkeypatch, next_offset):
    module = _load_fxmacrodata_module()
    response = _boundary_response({"data": [{"date": "2026-01-01", "val": 1.0}],
                                   "pagination": {"has_more": True, "next_offset": next_offset}})
    get = Mock(side_effect=[response, AssertionError("invalid next page attempted")])
    monkeypatch.setattr(module.requests, "get", get)
    with pytest.raises(ValueError):
        module.get_fxmacrodata_data("EURUSD", "2026-01-01", "2026-01-04")


def test_page_cap_does_not_silently_return_partial_history(monkeypatch):
    module = _load_fxmacrodata_module()
    monkeypatch.setattr(module, "FXMACRODATA_MAX_PAGES", 1)
    response = _boundary_response({"data": [{"date": "2026-01-01", "val": 1.0}],
                                   "pagination": {"has_more": True, "next_offset": 1}})
    monkeypatch.setattr(module.requests, "get", Mock(return_value=response))
    with pytest.raises(ValueError):
        module.get_fxmacrodata_data("EURUSD", "2026-01-01", "2026-01-04")


def test_private_transport_reason_is_not_chained(monkeypatch):
    import traceback
    module = _load_fxmacrodata_module()
    error = module.requests.ConnectionError("fixture-private-value")
    monkeypatch.setattr(module.requests, "get", Mock(side_effect=error))
    with pytest.raises(module.requests.RequestException) as raised:
        module.get_fxmacrodata_data("EURUSD", "2026-01-01", "2026-01-04")
    assert "fixture-private-value" not in "".join(traceback.format_exception(raised.value))


def _load_fxmacrodata_module():
    path = Path(__file__).parents[1] / "fastquant" / "data" / "fxmacrodata.py"
    spec = importlib.util.spec_from_file_location(
        "fastquant_fxmacrodata", path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_get_fxmacrodata_data(monkeypatch):
    class MockResponse:
        status_code = 200
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

    def mock_get(url, params, headers, timeout, allow_redirects=False):
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
    assert calls["params"]["limit"] == 100
    assert calls["params"]["offset"] == 0
    assert calls["headers"] == {"X-API-Key": "test-key"}
    assert list(df["close"]) == [1.1, 1.2]
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]


def test_get_fxmacrodata_data_follows_pagination(monkeypatch):
    pages = {
        0: {
            "data": [
                {"date": "2026-01-03", "val": 1.3},
                {"date": "2026-01-02", "val": 1.2},
            ],
            "pagination": {"has_more": True, "next_offset": 2},
        },
        2: {
            "data": [{"date": "2026-01-01", "val": 1.1}],
            "pagination": {"has_more": False, "next_offset": None},
        },
    }
    offsets = []

    class MockResponse:
        status_code = 200
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            pass

        def json(self):
            return self.payload

    def mock_get(url, params, headers, timeout, allow_redirects=False):
        offsets.append(params["offset"])
        return MockResponse(pages[params["offset"]])

    fxmacrodata = _load_fxmacrodata_module()
    monkeypatch.setattr(fxmacrodata.requests, "get", mock_get)
    df = fxmacrodata.get_fxmacrodata_data("EURUSD", "2026-01-01", "2026-01-03")

    assert offsets == [0, 2]
    assert list(df["close"]) == [1.1, 1.2, 1.3]
