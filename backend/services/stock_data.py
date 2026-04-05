"""
Stock Data Service
==================
Fetches Vietnamese stock market data with the following priority:
  1. DNSE / Entrade public API (no auth required)
  2. vnstock3
  3. yfinance
  4. Simulated data (always succeeds – keeps every endpoint functional offline)
"""

import hashlib
import logging
import random
from datetime import datetime, timedelta
from typing import Any

import httpx
import pandas as pd
from cachetools import TTLCache

logger = logging.getLogger("securities.stock_data")

# ---------------------------------------------------------------------------
# DNSE / Entrade base URL
# ---------------------------------------------------------------------------
DNSE_BASE_URL = "https://services.entrade.com.vn"

# ---------------------------------------------------------------------------
# Cache setup  (5-minute TTL, max 256 entries)
# ---------------------------------------------------------------------------
_cache: TTLCache = TTLCache(maxsize=256, ttl=300)

# ---------------------------------------------------------------------------
# Top 50 Vietnamese stocks – symbol, name, exchange, sector
# ---------------------------------------------------------------------------
VN_STOCKS = [
    {"symbol": "VNM",  "name": "Vinamilk",                             "exchange": "HOSE", "sector": "Tiêu dùng"},
    {"symbol": "FPT",  "name": "FPT Corporation",                      "exchange": "HOSE", "sector": "Công nghệ"},
    {"symbol": "VIC",  "name": "Vingroup",                             "exchange": "HOSE", "sector": "Bất động sản"},
    {"symbol": "VHM",  "name": "Vinhomes",                             "exchange": "HOSE", "sector": "Bất động sản"},
    {"symbol": "HPG",  "name": "Hòa Phát Group",                      "exchange": "HOSE", "sector": "Công nghiệp"},
    {"symbol": "MSN",  "name": "Masan Group",                          "exchange": "HOSE", "sector": "Tiêu dùng"},
    {"symbol": "MWG",  "name": "Mobile World Group",                   "exchange": "HOSE", "sector": "Bán lẻ"},
    {"symbol": "TCB",  "name": "Techcombank",                          "exchange": "HOSE", "sector": "Ngân hàng"},
    {"symbol": "VPB",  "name": "VPBank",                               "exchange": "HOSE", "sector": "Ngân hàng"},
    {"symbol": "ACB",  "name": "ACB Bank",                             "exchange": "HOSE", "sector": "Ngân hàng"},
    {"symbol": "BID",  "name": "BIDV",                                 "exchange": "HOSE", "sector": "Ngân hàng"},
    {"symbol": "CTG",  "name": "VietinBank",                           "exchange": "HOSE", "sector": "Ngân hàng"},
    {"symbol": "VCB",  "name": "Vietcombank",                          "exchange": "HOSE", "sector": "Ngân hàng"},
    {"symbol": "SSI",  "name": "SSI Securities",                       "exchange": "HOSE", "sector": "Chứng khoán"},
    {"symbol": "VND",  "name": "VNDirect Securities",                  "exchange": "HOSE", "sector": "Chứng khoán"},
    {"symbol": "HDB",  "name": "HDBank",                               "exchange": "HOSE", "sector": "Ngân hàng"},
    {"symbol": "STB",  "name": "Sacombank",                            "exchange": "HOSE", "sector": "Ngân hàng"},
    {"symbol": "MBB",  "name": "MB Bank",                              "exchange": "HOSE", "sector": "Ngân hàng"},
    {"symbol": "LPB",  "name": "LienVietPostBank",                     "exchange": "HOSE", "sector": "Ngân hàng"},
    {"symbol": "EIB",  "name": "Eximbank",                             "exchange": "HOSE", "sector": "Ngân hàng"},
    {"symbol": "GAS",  "name": "PV GAS",                               "exchange": "HOSE", "sector": "Năng lượng"},
    {"symbol": "PLX",  "name": "Petrolimex",                           "exchange": "HOSE", "sector": "Năng lượng"},
    {"symbol": "POW",  "name": "PV Power",                             "exchange": "HOSE", "sector": "Năng lượng"},
    {"symbol": "REE",  "name": "Refrigeration Engineering",            "exchange": "HOSE", "sector": "Công nghiệp"},
    {"symbol": "SAB",  "name": "Sabeco",                               "exchange": "HOSE", "sector": "Tiêu dùng"},
    {"symbol": "DGC",  "name": "Ducgiang Chemicals",                   "exchange": "HOSE", "sector": "Hóa chất"},
    {"symbol": "DCM",  "name": "Phân bón Cà Mau",                      "exchange": "HOSE", "sector": "Hóa chất"},
    {"symbol": "DPM",  "name": "PetroVietnam Fertilizer",              "exchange": "HOSE", "sector": "Hóa chất"},
    {"symbol": "GMD",  "name": "Gemadept",                             "exchange": "HOSE", "sector": "Logistics"},
    {"symbol": "PNJ",  "name": "Phú Nhuận Jewelry",                   "exchange": "HOSE", "sector": "Bán lẻ"},
    {"symbol": "KDH",  "name": "Khang Điền House",                    "exchange": "HOSE", "sector": "Bất động sản"},
    {"symbol": "NVL",  "name": "Novaland",                             "exchange": "HOSE", "sector": "Bất động sản"},
    {"symbol": "PDR",  "name": "Phát Đạt Real Estate",                "exchange": "HOSE", "sector": "Bất động sản"},
    {"symbol": "DXG",  "name": "Đất Xanh Group",                      "exchange": "HOSE", "sector": "Bất động sản"},
    {"symbol": "VRE",  "name": "Vincom Retail",                        "exchange": "HOSE", "sector": "Bất động sản"},
    {"symbol": "IJC",  "name": "Becamex IJC",                          "exchange": "HOSE", "sector": "Bất động sản"},
    {"symbol": "BCM",  "name": "Becamex IDC",                          "exchange": "HOSE", "sector": "Bất động sản"},
    {"symbol": "VGC",  "name": "Viglacera",                            "exchange": "HOSE", "sector": "Vật liệu XD"},
    {"symbol": "HSG",  "name": "Hoa Sen Group",                        "exchange": "HOSE", "sector": "Công nghiệp"},
    {"symbol": "NKG",  "name": "Nam Kim Steel",                        "exchange": "HOSE", "sector": "Công nghiệp"},
    {"symbol": "TVS",  "name": "Thiên Việt Securities",                "exchange": "HNX",  "sector": "Chứng khoán"},
    {"symbol": "SHS",  "name": "Saigon-Hanoi Securities",              "exchange": "HNX",  "sector": "Chứng khoán"},
    {"symbol": "PVS",  "name": "PetroVietnam Technical Services",      "exchange": "HNX",  "sector": "Năng lượng"},
    {"symbol": "HUT",  "name": "Tasco",                                "exchange": "HNX",  "sector": "Giao thông"},
    {"symbol": "PVC",  "name": "PetroVietnam Coating",                 "exchange": "HNX",  "sector": "Hóa chất"},
    {"symbol": "VCS",  "name": "VICOSTONE",                            "exchange": "HNX",  "sector": "Vật liệu XD"},
    {"symbol": "IDC",  "name": "Kinh Bắc City Development",            "exchange": "HNX",  "sector": "Bất động sản"},
    {"symbol": "NDN",  "name": "Da Nang Investment & Development",     "exchange": "HNX",  "sector": "Bất động sản"},
    {"symbol": "CEO",  "name": "CEO Group",                            "exchange": "HNX",  "sector": "Bất động sản"},
    {"symbol": "L14",  "name": "Licogi 14",                            "exchange": "HNX",  "sector": "Xây dựng"},
]

_STOCK_MAP: dict[str, dict] = {s["symbol"]: s for s in VN_STOCKS}

# Realistic base prices (VND) per symbol – used for simulated data seed
_BASE_PRICES: dict[str, float] = {
    "VNM": 72000, "FPT": 125000, "VIC": 38000, "VHM": 31000, "HPG": 27000,
    "MSN": 65000, "MWG": 55000, "TCB": 22000, "VPB": 18000, "ACB": 24000,
    "BID": 43000, "CTG": 32000, "VCB": 88000, "SSI": 26000, "VND": 17000,
    "HDB": 19000, "STB": 26000, "MBB": 20000, "LPB": 16000, "EIB": 17000,
    "GAS": 82000, "PLX": 40000, "POW": 11000, "REE": 50000, "SAB": 56000,
    "DGC": 72000, "DCM": 21000, "DPM": 24000, "GMD": 60000, "PNJ": 82000,
    "KDH": 29000, "NVL": 10000, "PDR": 14000, "DXG": 10000, "VRE": 28000,
    "IJC": 11000, "BCM": 44000, "VGC": 18000, "HSG": 20000, "NKG": 15000,
    "TVS": 12000, "SHS": 13000, "PVS": 19000, "HUT": 10000, "PVC": 10000,
    "VCS": 54000, "IDC": 38000, "NDN": 12000, "CEO": 11000, "L14": 26000,
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _seed_for(symbol: str) -> int:
    """Deterministic seed from symbol name."""
    return int(hashlib.md5(symbol.encode()).hexdigest()[:8], 16)


def _simulate_history(symbol: str, days: int = 365) -> pd.DataFrame:
    """
    Generate realistic OHLCV history using Geometric Brownian Motion.
    """
    seed = _seed_for(symbol)
    rng = random.Random(seed)

    base = _BASE_PRICES.get(symbol, 30000)
    records = []
    current = base
    date = datetime.now() - timedelta(days=days)

    for _ in range(days):
        date = date + timedelta(days=1)
        # Skip weekends
        if date.weekday() >= 5:
            continue
        drift = 0.0003
        vol = rng.gauss(0, 0.018)
        change = drift + vol
        open_p = current
        close_p = round(current * (1 + change), -1)  # round to 10 VND
        close_p = max(close_p, 1000)
        high_p = round(max(open_p, close_p) * (1 + abs(rng.gauss(0, 0.007))), -1)
        low_p  = round(min(open_p, close_p) * (1 - abs(rng.gauss(0, 0.007))), -1)
        volume = int(rng.gauss(1_500_000, 600_000))
        volume = max(volume, 50_000)
        records.append({
            "time":   date.strftime("%Y-%m-%d"),
            "open":   open_p,
            "high":   high_p,
            "low":    low_p,
            "close":  close_p,
            "volume": volume,
        })
        current = close_p

    return pd.DataFrame(records)


def _df_to_records(df: pd.DataFrame) -> list[dict]:
    """Normalise a DataFrame into a list-of-dicts with standard column names."""
    col_map = {
        "time":   ["time", "date", "Date", "datetime", "Datetime"],
        "open":   ["open", "Open"],
        "high":   ["high", "High"],
        "low":    ["low", "Low"],
        "close":  ["close", "Close"],
        "volume": ["volume", "Volume"],
    }
    rename = {}
    for std, candidates in col_map.items():
        for c in candidates:
            if c in df.columns and std not in df.columns:
                rename[c] = std
                break
    df = df.rename(columns=rename)

    # Ensure we have a 'time' column
    if "time" not in df.columns and df.index.name in ("date", "Date", "datetime", "Datetime"):
        df = df.reset_index().rename(columns={df.index.name: "time"})

    records = []
    for _, row in df.iterrows():
        rec: dict[str, Any] = {
            "time":   str(row.get("time", "")),
            "open":   float(row.get("open",   0)),
            "high":   float(row.get("high",   0)),
            "low":    float(row.get("low",    0)),
            "close":  float(row.get("close",  0)),
            "volume": int(row.get("volume",   0)),
        }
        records.append(rec)
    return records


def _period_to_days(period: str) -> int:
    mapping = {"1d": 1, "5d": 5, "1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730, "5y": 1825}
    return mapping.get(period, 365)


# ---------------------------------------------------------------------------
# DNSE / Entrade helpers
# ---------------------------------------------------------------------------

def _fetch_dnse_history(symbol: str, days: int) -> list[dict]:
    """
    Fetch OHLCV history from DNSE (Entrade) chart API.

    Prices returned by DNSE are in units of 1 000 VND (e.g. 72.5 = 72 500 VND).
    We multiply every price field by 1 000 before returning so the rest of the
    app always works in raw VND units.

    Returns an empty list on any error so callers can fall through gracefully.
    """
    now = datetime.now()
    ts_to   = int(now.timestamp())
    ts_from = int((now - timedelta(days=days)).timestamp())

    url = (
        f"{DNSE_BASE_URL}/chart-api/v2/ohlcs/stock"
        f"?from={ts_from}&to={ts_to}&symbol={symbol}&resolution=1D"
    )

    with httpx.Client(timeout=10) as client:
        resp = client.get(url)
        resp.raise_for_status()

    data = resp.json()
    timestamps: list = data.get("t", [])
    opens:      list = data.get("o", [])
    highs:      list = data.get("h", [])
    lows:       list = data.get("l", [])
    closes:     list = data.get("c", [])
    volumes:    list = data.get("v", [])

    if not timestamps:
        return []

    records = []
    for i, ts in enumerate(timestamps):
        date_str = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
        records.append({
            "time":   date_str,
            "open":   float(opens[i])   * 1000,
            "high":   float(highs[i])   * 1000,
            "low":    float(lows[i])    * 1000,
            "close":  float(closes[i])  * 1000,
            "volume": int(volumes[i]),
        })

    logger.debug("DNSE history: %s → %d candles", symbol, len(records))
    return records


def _fetch_dnse_index(symbol: str, days: int = 2) -> dict | None:
    """
    Fetch the latest OHLCV bar for a market index (VNINDEX / HNXINDEX).

    Index values from DNSE are in raw points (not 1 000-unit), so no scaling.
    Returns None on any error.
    """
    now = datetime.now()
    ts_to   = int(now.timestamp())
    ts_from = int((now - timedelta(days=days)).timestamp())

    url = (
        f"{DNSE_BASE_URL}/chart-api/v2/ohlcs/index"
        f"?from={ts_from}&to={ts_to}&symbol={symbol}&resolution=1D"
    )

    with httpx.Client(timeout=10) as client:
        resp = client.get(url)
        resp.raise_for_status()

    data = resp.json()
    timestamps: list = data.get("t", [])
    closes:     list = data.get("c", [])
    opens:      list = data.get("o", [])
    volumes:    list = data.get("v", [])

    if not timestamps:
        return None

    last_idx = len(timestamps) - 1
    close = float(closes[last_idx])
    open_ = float(opens[last_idx])
    change = close - open_
    change_pct = change / open_ * 100 if open_ else 0.0

    return {
        "value":      round(close, 2),
        "change":     round(change, 2),
        "change_pct": round(change_pct, 2),
        "volume":     int(volumes[last_idx]),
    }


def _fetch_dnse_market_overview() -> dict | None:
    """
    Fetch VNINDEX and HNXINDEX from DNSE and return the market overview dict.

    DNSE uses "VNINDEX" for VN-Index but "HNX" (not "HNXINDEX") for HNX-Index.
    Returns None if either index fetch fails.
    """
    vnindex  = _fetch_dnse_index("VNINDEX", days=5)
    hnxindex = _fetch_dnse_index("HNX",     days=5)

    if not vnindex or not hnxindex:
        return None

    return {
        "vnindex":    vnindex,
        "hnxindex":   hnxindex,
        "updated_at": datetime.now().isoformat(),
    }


def _fetch_dnse_stock_prices(symbols: list[str]) -> dict[str, float]:
    """
    Fetch the most-recent closing price (in VND) for each symbol via DNSE.

    We fetch the last 5 trading days per symbol and return the last close.
    Results are cached under 'dnse_price:<SYMBOL>' so repeated calls within
    the TTL window are free.  Returns only the symbols that succeeded.
    """
    prices: dict[str, float] = {}
    for sym in symbols:
        cache_key = f"dnse_price:{sym}"
        if cache_key in _cache:
            prices[sym] = _cache[cache_key]
            continue
        try:
            records = _fetch_dnse_history(sym, days=7)
            if records:
                last_close = records[-1]["close"]
                _cache[cache_key] = last_close
                prices[sym] = last_close
        except Exception as exc:
            logger.debug("DNSE price fetch failed for %s: %s", sym, exc)
    return prices


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_stock_list() -> list[dict]:
    """Return list of popular Vietnamese stocks with basic info."""
    cache_key = "stock_list"
    if cache_key in _cache:
        return _cache[cache_key]

    # Build base result with simulated prices first (always succeeds)
    result = []
    for stock in VN_STOCKS:
        sym = stock["symbol"]
        seed = _seed_for(sym)
        rng = random.Random(seed + 999)
        base = _BASE_PRICES.get(sym, 30000)
        change_pct = rng.gauss(0.3, 1.8)
        price = round(base * (1 + change_pct / 100), -1)
        result.append({
            "symbol":     sym,
            "name":       stock["name"],
            "exchange":   stock["exchange"],
            "sector":     stock["sector"],
            "price":      price,
            "change":     round(price * change_pct / 100, -1),
            "change_pct": round(change_pct, 2),
            "volume":     int(rng.gauss(1_500_000, 600_000)),
        })

    # --- Try DNSE real prices ---
    try:
        symbols = [s["symbol"] for s in VN_STOCKS]
        real_prices = _fetch_dnse_stock_prices(symbols)
        if real_prices:
            for item in result:
                sym = item["symbol"]
                if sym in real_prices:
                    real_price = real_prices[sym]
                    # Fetch previous close from DNSE 7-day history for accurate change
                    prev_close = real_price  # fallback
                    try:
                        hist = _fetch_dnse_history(sym, 7)
                        if hist and len(hist) >= 2:
                            prev_close = hist[-2]["close"]
                        elif hist and len(hist) == 1:
                            prev_close = hist[0]["open"]
                    except Exception:
                        pass
                    change = round(real_price - prev_close, -1)
                    change_pct = round((real_price - prev_close) / prev_close * 100, 2) if prev_close else 0.0
                    item["price"]      = real_price
                    item["change"]     = change
                    item["change_pct"] = change_pct
            logger.info("DNSE prices applied to stock list (%d/%d)", len(real_prices), len(symbols))
    except Exception as exc:
        logger.warning("DNSE stock-list price fetch failed: %s", exc)

    _cache[cache_key] = result
    return result


def get_stock_history(symbol: str, period: str = "1y") -> list[dict]:
    """
    Return historical OHLCV data for a symbol.
    Priority: DNSE → vnstock3 → yfinance → simulation.
    """
    cache_key = f"history:{symbol}:{period}"
    if cache_key in _cache:
        return _cache[cache_key]

    symbol = symbol.upper()
    days = _period_to_days(period)
    end_date   = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    # --- Try DNSE (Entrade) ---
    try:
        records = _fetch_dnse_history(symbol, days)
        if records:
            logger.info("DNSE history: %s (%s) → %d records", symbol, period, len(records))
            _cache[cache_key] = records
            return records
    except Exception as exc:
        logger.debug("DNSE history failed for %s: %s", symbol, exc)

    # --- Try vnstock3 ---
    try:
        from vnstock3 import Vnstock  # noqa: PLC0415
        vs = Vnstock().stock(symbol=symbol, source="VCI")
        df = vs.quote.history(start=start_date, end=end_date)
        if df is not None and not df.empty:
            records = _df_to_records(df)
            if records:
                _cache[cache_key] = records
                return records
    except Exception:
        pass

    # --- Try yfinance ---
    try:
        import yfinance as yf  # noqa: PLC0415
        ticker_sym = f"{symbol}.VN" if symbol in _STOCK_MAP else symbol
        tkr = yf.Ticker(ticker_sym)
        df = tkr.history(period=period)
        if df is not None and not df.empty:
            records = _df_to_records(df)
            if records:
                _cache[cache_key] = records
                return records
    except Exception:
        pass

    # --- Simulation fallback ---
    df = _simulate_history(symbol, days)
    records = df.to_dict("records")
    _cache[cache_key] = records
    return records


def get_stock_info(symbol: str) -> dict:
    """Return stock detail: name, exchange, sector, market_cap, and latest price."""
    cache_key = f"info:{symbol}"
    if cache_key in _cache:
        return _cache[cache_key]

    symbol = symbol.upper()
    base_info = _STOCK_MAP.get(symbol, {
        "symbol":   symbol,
        "name":     symbol,
        "exchange": "HOSE",
        "sector":   "Khác",
    })

    price_info: dict = {}

    # --- Try DNSE (latest close from last 5 days of history) ---
    try:
        records = _fetch_dnse_history(symbol, days=7)
        if records:
            last_close = records[-1]["close"]
            price_info["price"] = last_close
            logger.info("DNSE info price: %s → %.0f VND", symbol, last_close)
    except Exception as exc:
        logger.debug("DNSE info price failed for %s: %s", symbol, exc)

    # --- Try vnstock3 (if DNSE didn't give us a price) ---
    if not price_info:
        try:
            from vnstock3 import Vnstock  # noqa: PLC0415
            vs = Vnstock().stock(symbol=symbol, source="VCI")
            cmp = vs.trading.price_board(symbols_list=[symbol])
            if cmp is not None and not cmp.empty:
                row = cmp.iloc[0]
                price_info["price"] = float(row.get("close", row.get("match_price", 0)))
                price_info["market_cap"] = float(row.get("market_cap", 0))
        except Exception:
            pass

    if not price_info:
        # Derive from simulated history
        hist = get_stock_history(symbol, period="5d")
        last = hist[-1] if hist else {}
        price_info["price"] = last.get("close", _BASE_PRICES.get(symbol, 30000))

    if "market_cap" not in price_info:
        rng = random.Random(_seed_for(symbol))
        shares = rng.randint(300_000_000, 5_000_000_000)
        price_info["market_cap"] = price_info["price"] * shares

    result = {
        **base_info,
        "price":      price_info.get("price", 0),
        "market_cap": price_info.get("market_cap", 0),
    }
    _cache[cache_key] = result
    return result


def get_market_overview() -> dict:
    """Return VN-Index and HNX-Index summary."""
    cache_key = "market_overview"
    if cache_key in _cache:
        return _cache[cache_key]

    # --- Try DNSE (Entrade) ---
    try:
        result = _fetch_dnse_market_overview()
        if result:
            logger.info(
                "DNSE market overview: VNINDEX=%.2f HNXINDEX=%.2f",
                result["vnindex"]["value"],
                result["hnxindex"]["value"],
            )
            _cache[cache_key] = result
            return result
    except Exception as exc:
        logger.debug("DNSE market overview failed: %s", exc)

    # --- Try vnstock3 market indices ---
    try:
        from vnstock3 import Vnstock  # noqa: PLC0415
        vs = Vnstock()
        idx = vs.stock(symbol="VNINDEX", source="VCI")
        df = idx.quote.history(
            start=(datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
            end=datetime.now().strftime("%Y-%m-%d"),
        )
        if df is not None and not df.empty:
            last = df.iloc[-1]
            vni_close = float(last.get("close", 1250))
            vni_open  = float(last.get("open",  vni_close))
            vni_chg   = vni_close - vni_open
            vni_chg_pct = vni_chg / vni_open * 100 if vni_open else 0
            result = {
                "vnindex": {
                    "value":      vni_close,
                    "change":     round(vni_chg, 2),
                    "change_pct": round(vni_chg_pct, 2),
                    "volume":     int(last.get("volume", 0)),
                },
                "hnxindex": {
                    "value":      240.0 + random.gauss(0, 2),
                    "change":     round(random.gauss(0.5, 1.5), 2),
                    "change_pct": round(random.gauss(0.2, 0.6), 2),
                    "volume":     random.randint(50_000_000, 150_000_000),
                },
                "updated_at": datetime.now().isoformat(),
            }
            _cache[cache_key] = result
            return result
    except Exception:
        pass

    # Simulated overview
    rng = random.Random(int(datetime.now().strftime("%Y%m%d")))
    vni = 1250 + rng.gauss(0, 15)
    vni_chg = rng.gauss(2, 8)
    result = {
        "vnindex": {
            "value":      round(vni, 2),
            "change":     round(vni_chg, 2),
            "change_pct": round(vni_chg / vni * 100, 2),
            "volume":     rng.randint(300_000_000, 700_000_000),
        },
        "hnxindex": {
            "value":      round(240 + rng.gauss(0, 3), 2),
            "change":     round(rng.gauss(0.5, 1.5), 2),
            "change_pct": round(rng.gauss(0.2, 0.6), 2),
            "volume":     rng.randint(50_000_000, 150_000_000),
        },
        "updated_at": datetime.now().isoformat(),
    }
    _cache[cache_key] = result
    return result
