"""
Technical Analysis Service
==========================
Computes common technical indicators using the `ta` library
(with pure-pandas manual fallbacks) and generates trading signals.
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure close/open/high/low/volume columns are numeric."""
    for col in ("close", "open", "high", "low", "volume"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["close"])


# ---------------------------------------------------------------------------
# Indicator calculators
# ---------------------------------------------------------------------------

def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Relative Strength Index.

    Returns a pd.Series aligned to df.index.
    """
    df = _ensure_numeric(df)
    try:
        import ta  # noqa: PLC0415
        return ta.momentum.RSIIndicator(df["close"], window=period).rsi()
    except Exception:
        pass

    # Manual Wilder smoothing
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, float("nan"))
    return 100 - (100 / (1 + rs))


def calculate_macd(df: pd.DataFrame) -> dict[str, pd.Series]:
    """
    MACD indicator.

    Returns dict with keys: macd, signal, histogram.
    """
    df = _ensure_numeric(df)
    try:
        import ta  # noqa: PLC0415
        ind = ta.trend.MACD(df["close"])
        return {
            "macd":      ind.macd(),
            "signal":    ind.macd_signal(),
            "histogram": ind.macd_diff(),
        }
    except Exception:
        pass

    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9, adjust=False).mean()
    return {
        "macd":      macd_line,
        "signal":    signal,
        "histogram": macd_line - signal,
    }


def calculate_bollinger(df: pd.DataFrame, period: int = 20) -> dict[str, pd.Series]:
    """
    Bollinger Bands.

    Returns dict with keys: upper, middle, lower, bandwidth, pct_b.
    """
    df = _ensure_numeric(df)
    try:
        import ta  # noqa: PLC0415
        ind = ta.volatility.BollingerBands(df["close"], window=period)
        return {
            "upper":     ind.bollinger_hband(),
            "middle":    ind.bollinger_mavg(),
            "lower":     ind.bollinger_lband(),
            "bandwidth": ind.bollinger_wband(),
            "pct_b":     ind.bollinger_pband(),
        }
    except Exception:
        pass

    middle = df["close"].rolling(window=period).mean()
    std = df["close"].rolling(window=period).std()
    upper = middle + 2 * std
    lower = middle - 2 * std
    bandwidth = (upper - lower) / middle
    pct_b = (df["close"] - lower) / (upper - lower)
    return {
        "upper":     upper,
        "middle":    middle,
        "lower":     lower,
        "bandwidth": bandwidth,
        "pct_b":     pct_b,
    }


def calculate_sma(df: pd.DataFrame, periods: list[int] | None = None) -> dict[str, pd.Series]:
    """
    Simple Moving Averages for requested periods.

    Returns dict keyed by 'sma_{period}'.
    """
    if periods is None:
        periods = [20, 50, 200]
    df = _ensure_numeric(df)
    return {f"sma_{p}": df["close"].rolling(window=p).mean() for p in periods}


def calculate_ema(df: pd.DataFrame, periods: list[int] | None = None) -> dict[str, pd.Series]:
    """
    Exponential Moving Averages for requested periods.

    Returns dict keyed by 'ema_{period}'.
    """
    if periods is None:
        periods = [12, 26]
    df = _ensure_numeric(df)
    return {f"ema_{p}": df["close"].ewm(span=p, adjust=False).mean() for p in periods}


def calculate_volume_indicators(df: pd.DataFrame) -> dict[str, pd.Series]:
    """OBV and volume SMA."""
    df = _ensure_numeric(df)
    try:
        import ta  # noqa: PLC0415
        obv = ta.volume.OnBalanceVolumeIndicator(df["close"], df["volume"]).on_balance_volume()
    except Exception:
        direction = df["close"].diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
        obv = (df["volume"] * direction).cumsum()

    return {
        "obv":        obv,
        "volume_sma": df["volume"].rolling(20).mean(),
    }


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range."""
    df = _ensure_numeric(df)
    try:
        import ta  # noqa: PLC0415
        return ta.volatility.AverageTrueRange(df["high"], df["low"], df["close"], window=period).average_true_range()
    except Exception:
        pass
    hl = df["high"] - df["low"]
    hc = (df["high"] - df["close"].shift()).abs()
    lc = (df["low"]  - df["close"].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def calculate_all_indicators(df: pd.DataFrame) -> dict[str, Any]:
    """
    Compute all indicators and return their **latest** scalar values.

    Returns a flat dict suitable for JSON serialisation.
    """
    df = _ensure_numeric(df)
    if df.empty or len(df) < 5:
        return {}

    close = df["close"]
    last_close = float(close.iloc[-1])

    def last(series: pd.Series) -> float | None:
        try:
            v = series.dropna().iloc[-1]
            return round(float(v), 4) if not (math.isnan(float(v)) or math.isinf(float(v))) else None
        except (IndexError, ValueError):
            return None

    rsi_s = calculate_rsi(df)
    macd_d = calculate_macd(df)
    boll_d = calculate_bollinger(df)
    sma_d  = calculate_sma(df)
    ema_d  = calculate_ema(df)
    vol_d  = calculate_volume_indicators(df)
    atr_s  = calculate_atr(df)

    result: dict[str, Any] = {
        "close": last_close,
        "rsi":   last(rsi_s),
        "macd":  last(macd_d["macd"]),
        "macd_signal":    last(macd_d["signal"]),
        "macd_histogram": last(macd_d["histogram"]),
        "bb_upper":  last(boll_d["upper"]),
        "bb_middle": last(boll_d["middle"]),
        "bb_lower":  last(boll_d["lower"]),
        "bb_pct_b":  last(boll_d["pct_b"]),
        "atr":       last(atr_s),
        "obv":       last(vol_d["obv"]),
        "volume_sma": last(vol_d["volume_sma"]),
    }
    for k, v in sma_d.items():
        result[k] = last(v)
    for k, v in ema_d.items():
        result[k] = last(v)

    return result


# ---------------------------------------------------------------------------
# Signal generation
# ---------------------------------------------------------------------------

def generate_signal(indicators: dict[str, Any]) -> dict[str, Any]:
    """
    Produce a Buy / Sell / Hold signal from latest indicator values.

    Returns:
        {
            "signal":     "Buy" | "Sell" | "Hold",
            "confidence": 0.0 – 1.0,
            "reasons":    [str, ...]
        }
    """
    score = 0.0
    reasons: list[str] = []
    weights = 0.0

    close = indicators.get("close") or 0.0

    # --- RSI ---
    rsi = indicators.get("rsi")
    if rsi is not None:
        weights += 2
        if rsi < 30:
            score += 2;  reasons.append(f"RSI={rsi:.1f} (quá bán - cơ hội mua)")
        elif rsi > 70:
            score -= 2;  reasons.append(f"RSI={rsi:.1f} (quá mua - cân nhắc bán)")
        elif rsi < 45:
            score += 0.5; reasons.append(f"RSI={rsi:.1f} (xu hướng tăng)")
        elif rsi > 55:
            score -= 0.5; reasons.append(f"RSI={rsi:.1f} (xu hướng giảm)")

    # --- MACD ---
    macd   = indicators.get("macd")
    signal = indicators.get("macd_signal")
    hist   = indicators.get("macd_histogram")
    if macd is not None and signal is not None:
        weights += 2
        if macd > signal:
            score += 2; reasons.append("MACD cắt lên đường tín hiệu (tín hiệu mua)")
        else:
            score -= 2; reasons.append("MACD cắt xuống đường tín hiệu (tín hiệu bán)")
        if hist is not None and hist > 0:
            score += 0.5; reasons.append("Biểu đồ MACD dương (đà tăng)")

    # --- Bollinger Bands ---
    pct_b = indicators.get("bb_pct_b")
    if pct_b is not None:
        weights += 1
        if pct_b < 0.2:
            score += 1; reasons.append(f"%B={pct_b:.2f} (giá gần band dưới - quá bán)")
        elif pct_b > 0.8:
            score -= 1; reasons.append(f"%B={pct_b:.2f} (giá gần band trên - quá mua)")

    # --- SMA trend ---
    sma20 = indicators.get("sma_20")
    sma50 = indicators.get("sma_50")
    if close and sma20:
        weights += 1.5
        if close > sma20:
            score += 1; reasons.append("Giá trên SMA20 (xu hướng tăng ngắn hạn)")
        else:
            score -= 1; reasons.append("Giá dưới SMA20 (xu hướng giảm ngắn hạn)")
    if sma20 and sma50:
        weights += 1
        if sma20 > sma50:
            score += 1; reasons.append("SMA20 > SMA50 (Golden Cross)")
        else:
            score -= 1; reasons.append("SMA20 < SMA50 (Death Cross)")

    if weights == 0:
        return {"signal": "Hold", "confidence": 0.5, "reasons": ["Không đủ dữ liệu"]}

    normalised = score / weights  # in [-1, 1]
    confidence = round(abs(normalised) * 0.5 + 0.5, 2)  # [0.5, 1.0]
    confidence = min(confidence, 0.95)

    if normalised > 0.2:
        sig = "Buy"
    elif normalised < -0.2:
        sig = "Sell"
    else:
        sig = "Hold"
        confidence = round(0.5 + abs(normalised) * 0.2, 2)

    return {"signal": sig, "confidence": confidence, "reasons": reasons[:5]}
