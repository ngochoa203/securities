"""
Stock Routes
============
GET /api/stocks            – List all available stocks
GET /api/stocks/{symbol}   – Stock detail with recent history
GET /api/stocks/{symbol}/predict   – AI ensemble prediction
GET /api/stocks/{symbol}/technical – Technical indicators + signal
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from services.stock_data import (
    VN_STOCKS,
    get_stock_history,
    get_stock_info,
    get_market_overview,
)
from services.technical import calculate_all_indicators, generate_signal
from models.ensemble import EnsemblePredictor

router = APIRouter(prefix="/api/stocks", tags=["stocks"])

_ensemble = EnsemblePredictor()


# ---------------------------------------------------------------------------
# GET /api/stocks
# ---------------------------------------------------------------------------

@router.get("", summary="List all available Vietnamese stocks")
async def list_stocks(
    exchange: str | None = Query(default=None, description="Filter by exchange: HOSE / HNX / UPCOM"),
    sector:   str | None = Query(default=None, description="Filter by sector"),
) -> dict[str, Any]:
    """
    Returns the full list of tracked Vietnamese stocks with
    basic price info (price / change / change_pct).
    """
    from services.stock_data import get_stock_list  # noqa: PLC0415
    stocks = get_stock_list()

    if exchange:
        stocks = [s for s in stocks if s.get("exchange", "").upper() == exchange.upper()]
    if sector:
        stocks = [s for s in stocks if sector.lower() in s.get("sector", "").lower()]

    market = get_market_overview()
    return {
        "total":   len(stocks),
        "stocks":  stocks,
        "market":  market,
    }


# ---------------------------------------------------------------------------
# GET /api/stocks/{symbol}
# ---------------------------------------------------------------------------

@router.get("/{symbol}", summary="Stock detail with historical OHLCV")
async def get_stock(
    symbol: str,
    period: str = Query(default="1y", description="1d|5d|1mo|3mo|6mo|1y|2y|5y"),
) -> dict[str, Any]:
    """
    Returns stock metadata and full OHLCV history for the requested period.
    Flat response format matching frontend StockDetail interface.
    """
    symbol = symbol.upper()
    info    = get_stock_info(symbol)
    history = get_stock_history(symbol, period=period)

    if not history:
        raise HTTPException(status_code=404, detail=f"No data found for symbol {symbol}")

    # Normalise history: frontend expects "date" key, backend may use "time"
    normalised_history = []
    for rec in history:
        normalised_history.append({
            "date":   rec.get("date", rec.get("time", "")),
            "open":   rec.get("open", 0),
            "high":   rec.get("high", 0),
            "low":    rec.get("low", 0),
            "close":  rec.get("close", 0),
            "volume": rec.get("volume", 0),
        })

    # Compute change from last two data points
    last_close = normalised_history[-1]["close"] if normalised_history else 0
    prev_close = normalised_history[-2]["close"] if len(normalised_history) >= 2 else last_close
    change = round(last_close - prev_close, 2)
    change_pct = round((change / prev_close * 100) if prev_close else 0, 2)

    # Last volume
    last_volume = normalised_history[-1]["volume"] if normalised_history else 0

    return {
        "symbol":     symbol,
        "name":       info.get("name", symbol),
        "exchange":   info.get("exchange", "HOSE"),
        "sector":     info.get("sector", "Khác"),
        "price":      last_close,
        "change":     change,
        "change_pct": change_pct,
        "volume":     last_volume,
        "market_cap": info.get("market_cap", 0),
        "history":    normalised_history,
    }


# ---------------------------------------------------------------------------
# GET /api/stocks/{symbol}/predict
# ---------------------------------------------------------------------------

@router.get("/{symbol}/predict", summary="AI ensemble price prediction")
async def predict_stock(
    symbol:        str,
    period:        str = Query(default="1y",  description="Training data period"),
    forecast_days: int = Query(default=7,     description="Days to forecast (max 30)"),
) -> dict[str, Any]:
    """
    Runs LSTM + XGBoost + Prophet ensemble and returns a blended
    price forecast for days 1, 7, and 30.
    """
    symbol = symbol.upper()
    forecast_days = min(max(forecast_days, 1), 30)

    try:
        result = _ensemble.predict(symbol, period=period, forecast_days=forecast_days)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") from exc

    return result


# ---------------------------------------------------------------------------
# GET /api/stocks/{symbol}/technical
# ---------------------------------------------------------------------------

@router.get("/{symbol}/technical", summary="Technical analysis indicators and signal")
async def get_technical(
    symbol: str,
    period: str = Query(default="6mo", description="Data period for indicator calculation"),
) -> dict[str, Any]:
    """
    Returns all technical indicators (RSI, MACD, Bollinger, SMA, EMA)
    and a derived Buy / Sell / Hold signal with confidence.
    """
    symbol = symbol.upper()
    history = get_stock_history(symbol, period=period)

    if not history:
        raise HTTPException(status_code=404, detail=f"No data for {symbol}")

    df = pd.DataFrame(history)
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["close"])

    raw_indicators = calculate_all_indicators(df)
    signal_data    = generate_signal(raw_indicators)

    # Reshape indicators to match frontend TechnicalResult interface
    indicators_shaped = {
        "rsi": raw_indicators.get("rsi", 50),
        "macd": {
            "line":      raw_indicators.get("macd", 0),
            "signal":    raw_indicators.get("macd_signal", 0),
            "histogram": raw_indicators.get("macd_histogram", 0),
        },
        "bollinger": {
            "upper":  raw_indicators.get("bb_upper", 0),
            "middle": raw_indicators.get("bb_middle", 0),
            "lower":  raw_indicators.get("bb_lower", 0),
        },
        "sma": {
            "sma_20":  raw_indicators.get("sma_20", 0),
            "sma_50":  raw_indicators.get("sma_50", 0),
            "sma_200": raw_indicators.get("sma_200", 0),
        },
        "ema": {
            "ema_12": raw_indicators.get("ema_12", 0),
            "ema_26": raw_indicators.get("ema_26", 0),
            "ema_50": raw_indicators.get("ema_50", 0),
        },
    }

    return {
        "symbol":           symbol,
        "period":           period,
        "indicators":       indicators_shaped,
        "signal":           signal_data.get("signal", "Hold"),
        "signal_confidence": signal_data.get("confidence", 0.5),
        "reasons":          signal_data.get("reasons", []),
    }
