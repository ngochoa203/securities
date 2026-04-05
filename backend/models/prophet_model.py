"""
Prophet Predictor
=================
Uses Facebook Prophet for time-series forecasting.
Falls back to simple exponential smoothing when Prophet
is not installed or training fails.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Fallback: simple exponential smoothing (Holt-Winters single)
# ---------------------------------------------------------------------------

def _exp_smooth_predict(close: np.ndarray, days: int, alpha: float = 0.3) -> list[float]:
    """One-pass exponential smoothing extrapolated forward."""
    s = float(close[0])
    for v in close[1:]:
        s = alpha * float(v) + (1 - alpha) * s

    # Linear trend from last 10 points
    tail = close[-min(10, len(close)):]
    if len(tail) > 1:
        slope = float(np.polyfit(np.arange(len(tail)), tail, 1)[0])
    else:
        slope = 0.0

    prices: list[float] = []
    current = s
    for i in range(days):
        current = current + slope + (alpha * slope * i * 0.1)
        current = max(current, 500.0)
        prices.append(round(float(current), -1))
    return prices


# ---------------------------------------------------------------------------
# Prophet predictor
# ---------------------------------------------------------------------------

class ProphetPredictor:
    """
    Wraps Facebook Prophet.  Falls back to exponential smoothing
    when Prophet is unavailable or throws an error.
    """

    def predict(self, df: pd.DataFrame, days: int = 7) -> dict[str, Any]:
        """
        Predict the next `days` closing prices.

        Parameters
        ----------
        df   : DataFrame with at minimum a 'close' column (and optionally 'time')
        days : Number of future trading days to forecast

        Returns
        -------
        dict with keys: prices, direction, confidence, model
        """
        df = df.copy()
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df.dropna(subset=["close"])
        close_arr = df["close"].values.astype(float)

        if len(df) < 10:
            prices = _exp_smooth_predict(close_arr if len(close_arr) else np.array([30_000.0]), days)
            return self._result(prices, float(close_arr[-1]) if len(close_arr) else prices[0], "Prophet (fallback – insufficient data)")

        # --- Build Prophet-compatible DataFrame ---
        if "time" in df.columns:
            try:
                prophet_df = pd.DataFrame({
                    "ds": pd.to_datetime(df["time"]),
                    "y":  close_arr,
                })
            except Exception:
                prophet_df = None
        else:
            prophet_df = None

        if prophet_df is None or prophet_df.empty:
            # Create synthetic dates
            prophet_df = pd.DataFrame({
                "ds": pd.date_range(end=pd.Timestamp.today(), periods=len(close_arr), freq="B"),
                "y":  close_arr,
            })

        prophet_df = prophet_df.dropna()

        # --- Try Prophet ---
        try:
            from prophet import Prophet  # noqa: PLC0415
            import logging  # noqa: PLC0415
            logging.getLogger("prophet").setLevel(logging.ERROR)
            logging.getLogger("cmdstanpy").setLevel(logging.ERROR)

            model = Prophet(
                daily_seasonality=False,
                weekly_seasonality=True,
                yearly_seasonality=True,
                changepoint_prior_scale=0.05,
                seasonality_prior_scale=10,
                uncertainty_samples=0,   # disable MCMC for speed
            )
            model.fit(prophet_df)

            future = model.make_future_dataframe(periods=days, freq="B")
            forecast = model.predict(future)
            pred_rows = forecast.tail(days)
            prices = [round(max(float(p), 500.0), -1) for p in pred_rows["yhat"].tolist()]

            return self._result(prices, float(close_arr[-1]), "Prophet")

        except Exception:
            pass

        # --- Exponential smoothing fallback ---
        prices = _exp_smooth_predict(close_arr, days)
        return self._result(prices, float(close_arr[-1]), "Prophet (exp-smoothing fallback)")

    # ------------------------------------------------------------------
    @staticmethod
    def _result(prices: list[float], last_price: float, model_name: str) -> dict[str, Any]:
        if not prices:
            prices = [last_price]
        pct = (prices[-1] - last_price) / last_price if last_price else 0
        direction  = "up" if pct > 0 else "down"
        confidence = round(min(abs(pct) * 8 + 0.50, 0.90), 2)
        return {
            "prices":     prices,
            "direction":  direction,
            "confidence": confidence,
            "model":      model_name,
        }
