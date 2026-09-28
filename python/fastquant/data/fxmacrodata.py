import os

import pandas as pd
import requests


FXMACRODATA_API_ROOT = "https://api.fxmacrodata.com/v1"
# The API returns at most 100 rows per request, newest first.
FXMACRODATA_PAGE_SIZE = 100
FXMACRODATA_MAX_PAGES = 1000


def _split_pair(pair):
    pair = pair.upper().replace("/", "").replace("-", "").replace("_", "")
    if len(pair) != 6:
        raise ValueError(
            "FX pair must be formatted like 'EURUSD' or 'EUR/USD'"
        )
    return pair[:3], pair[3:]


def get_fxmacrodata_data(
    pair,
    start_date,
    end_date,
    api_key=None,
    api_root=FXMACRODATA_API_ROOT,
):
    """Return daily FX reference rates from FXMacroData in OHLCV format.

    FXMacroData serves official daily reference rates as one value per date.
    The value is mapped to open, high, low, close, and volume is set to zero so
    the result can be passed directly to fastquant's backtesting helpers.
    """
    base, quote = _split_pair(pair)
    api_key = api_key or os.environ.get("FXMACRODATA_API_KEY")
    headers = {"X-API-Key": api_key} if api_key else {}
    url = "{}/forex/{}/{}".format(api_root.rstrip("/"), base, quote)

    rows = []
    offset = 0
    for _ in range(FXMACRODATA_MAX_PAGES):
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "limit": FXMACRODATA_PAGE_SIZE,
            "offset": offset,
        }
        response = requests.get(
            url, params=params, headers=headers, timeout=30
        )
        response.raise_for_status()
        payload = response.json()
        page = payload.get("data", [])
        rows.extend(page)
        pagination = payload.get("pagination") or {}
        if not page or not pagination.get("has_more"):
            break
        offset = pagination.get("next_offset") or offset + len(page)

    records = []
    for row in rows:
        value = float(row["val"])
        records.append(
            {
                "dt": pd.to_datetime(row["date"]),
                "open": value,
                "high": value,
                "low": value,
                "close": value,
                "volume": 0.0,
            }
        )

    df = pd.DataFrame.from_records(records)
    if df.empty:
        return df

    df = df.drop_duplicates("dt").sort_values("dt").set_index("dt")
    df.start_date = start_date
    df.end_date = end_date
    df.symbol = "{}/{}".format(base, quote)
    return df
