"""
Rankings Engine
===============
Provides curated stock rankings:
  - top_buy       : strongest technical Buy signals
  - top_decline   : biggest recent price decliners (buy-the-dip)
  - trustworthy   : large-cap blue-chips
  - top_invest    : AI-recommended (technicals + prediction direction)
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from services.stock_data import VN_STOCKS, get_stock_history, _BASE_PRICES, _seed_for
from services.technical import calculate_all_indicators, generate_signal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _quick_stats(symbol: str) -> dict[str, Any]:
    """
    Return price, change, change_pct, signal, confidence, reasons
    from recent history (uses cached data when available).
    """
    history = get_stock_history(symbol, period="3mo")
    df = pd.DataFrame(history)
    if df.empty:
        base = _BASE_PRICES.get(symbol, 30_000)
        return {
            "price":      float(base),
            "change":     0.0,
            "change_pct": 0.0,
            "signal":     "Hold",
            "confidence": 0.5,
            "reasons":    [],
        }

    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["close"])

    current = float(df["close"].iloc[-1])
    prev    = float(df["close"].iloc[-2]) if len(df) > 1 else current
    change  = round(current - prev, -1)
    chg_pct = round((current - prev) / prev * 100, 2) if prev else 0.0

    indicators = calculate_all_indicators(df)
    sig = generate_signal(indicators)

    return {
        "price":      current,
        "change":     change,
        "change_pct": chg_pct,
        "signal":     sig["signal"],
        "confidence": sig["confidence"],
        "reasons":    sig.get("reasons", []),
    }


def _enrich(symbol: str, meta: dict) -> dict[str, Any]:
    """Merge stock metadata with quick stats."""
    stats = _quick_stats(symbol)
    return {
        "symbol":     symbol,
        "name":       meta.get("name", symbol),
        "exchange":   meta.get("exchange", "HOSE"),
        "sector":     meta.get("sector", "Khác"),
        **stats,
    }


_STOCK_META: dict[str, dict] = {s["symbol"]: s for s in VN_STOCKS}


# ---------------------------------------------------------------------------
# Blue-chip whitelist (hardcoded for trustworthy list)
# ---------------------------------------------------------------------------

_BLUE_CHIPS = [
    {"symbol": "VCB",  "reason": "Ngân hàng lớn nhất Việt Nam, cổ phiếu ổn định nhất thị trường"},
    {"symbol": "BID",  "reason": "BIDV – Ngân hàng quốc doanh có tài sản lớn nhất"},
    {"symbol": "CTG",  "reason": "VietinBank – Ổn định, thanh khoản cao"},
    {"symbol": "VNM",  "reason": "Vinamilk – Thương hiệu tiêu dùng số 1, lợi tức cổ tức ổn định"},
    {"symbol": "GAS",  "reason": "PV GAS – Độc quyền khí thiên nhiên, biên lợi nhuận cao"},
    {"symbol": "FPT",  "reason": "FPT – Công ty công nghệ hàng đầu, tăng trưởng bền vững"},
    {"symbol": "SAB",  "reason": "Sabeco – Thị phần bia lớn nhất, cổ tức đều đặn"},
    {"symbol": "MBB",  "reason": "MB Bank – Ngân hàng tư nhân tăng trưởng mạnh"},
    {"symbol": "ACB",  "reason": "ACB – Ngân hàng bán lẻ hiệu quả hàng đầu"},
    {"symbol": "TCB",  "reason": "Techcombank – Chiến lược số hoá dẫn đầu ngành"},
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_top_buy(limit: int = 10) -> list[dict]:
    """
    Stocks with the strongest Buy technical signals.
    """
    results = []
    candidates = [s["symbol"] for s in VN_STOCKS[:30]]  # scan top 30 for speed

    for sym in candidates:
        meta = _STOCK_META.get(sym, {"name": sym, "exchange": "HOSE", "sector": "Khác"})
        row = _enrich(sym, meta)
        if row["signal"] == "Buy":
            results.append(row)

    # Sort by confidence desc
    results.sort(key=lambda x: x["confidence"], reverse=True)

    # If not enough Buy signals, add Hold with best confidence
    if len(results) < limit:
        for sym in candidates:
            if sym in [r["symbol"] for r in results]:
                continue
            meta = _STOCK_META.get(sym, {})
            row = _enrich(sym, meta)
            if row["signal"] == "Hold":
                results.append(row)
            if len(results) >= limit:
                break

    return [_add_reason_field(r) for r in results[:limit]]


def get_top_decline(limit: int = 10) -> list[dict]:
    """
    Biggest recent price decliners sorted by change_pct ascending.
    Buy-the-dip candidates.
    """
    results = []
    for s in VN_STOCKS[:40]:
        sym = s["symbol"]
        meta = _STOCK_META.get(sym, {})
        row = _enrich(sym, meta)
        results.append(row)

    results.sort(key=lambda x: x["change_pct"])
    out = []
    for r in results[:limit]:
        r = dict(r)
        r["reason"] = f"Giảm {abs(r['change_pct']):.1f}% – Có thể là cơ hội mua đáy"
        out.append(r)
    return out


def get_trustworthy(limit: int = 10) -> list[dict]:
    """
    Large-cap, well-known blue-chip companies.
    """
    results = []
    for bc in _BLUE_CHIPS[:limit]:
        sym = bc["symbol"]
        meta = _STOCK_META.get(sym, {})
        row = _enrich(sym, meta)
        row["reason"] = bc["reason"]
        results.append(row)
    return results


def get_top_invest(limit: int = 10) -> list[dict]:
    """
    AI-recommended picks combining technical signal + prediction direction.
    Uses a composite score: confidence * signal_multiplier.
    """
    from models.ensemble import EnsemblePredictor  # noqa: PLC0415 (avoid circular at module load)
    ensemble = EnsemblePredictor()

    results = []
    candidates = [s["symbol"] for s in VN_STOCKS[:25]]  # Keep fast for demo

    for sym in candidates:
        meta = _STOCK_META.get(sym, {})
        row = _enrich(sym, meta)

        # Quick ensemble directional check (only 7 days, fast)
        try:
            pred = ensemble.predict(sym, period="6mo", forecast_days=7)
            pred_direction = pred.get("direction", "up")
            pred_conf      = float(pred.get("confidence", 0.5))
            pct_7d = (pred["predictions"].get("7", row["price"]) - row["price"]) / row["price"] * 100
        except Exception:
            pred_direction = "up"
            pred_conf = 0.5
            pct_7d = 0.0

        sig_mult = 1.0 if row["signal"] == "Buy" else (0.5 if row["signal"] == "Hold" else 0.1)
        ai_score = row["confidence"] * sig_mult * pred_conf

        row["ai_score"]       = round(ai_score, 3)
        row["pred_direction"] = pred_direction
        row["pred_change_7d"] = round(pct_7d, 2)
        row["reason"] = (
            f"Tín hiệu kỹ thuật: {row['signal']} | "
            f"AI dự báo: {'Tăng' if pred_direction=='up' else 'Giảm'} "
            f"{abs(pct_7d):.1f}% trong 7 ngày"
        )
        results.append(row)

    results.sort(key=lambda x: x["ai_score"], reverse=True)
    return results[:limit]


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _add_reason_field(row: dict) -> dict:
    """Add a human-readable reason if missing."""
    row = dict(row)
    if "reason" not in row:
        reasons = row.get("reasons", [])
        row["reason"] = reasons[0] if reasons else f"Tín hiệu {row.get('signal','Hold')} từ phân tích kỹ thuật"
    return row
