"""
LSTM Predictor (Statistical Approximation)
==========================================
Instead of training a real LSTM (too slow for a demo), this module uses
moving-average convergence + volatility-adjusted trend extrapolation to
mimic what an LSTM might output.  Results are deterministic given the
input data so repeated calls are stable.
"""

from __future__ import annotations

import math
import random
from typing import Any

import numpy as np
import pandas as pd


class LSTMPredictor:
    """
    Pseudo-LSTM predictor based on:
      - Exponential trend from last N candles
      - Volatility-adjusted noise sampled from recent std-dev
      - Mean-reversion toward the 20-day EMA
    """

    def __init__(self, lookback: int = 30):
        self.lookback = lookback

    # ------------------------------------------------------------------
    def predict(self, df: pd.DataFrame, days: int = 7) -> dict[str, Any]:
        """
        Generate predicted prices for the next `days` trading days.

        Parameters
        ----------
        df   : DataFrame with at minimum a 'close' column
        days : Number of future trading days to forecast

        Returns
        -------
        dict with keys: prices, direction, confidence, model
        """
        df = df.copy()
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df.dropna(subset=["close"])

        if len(df) < 5:
            # Insufficient data – return flat forecast
            last = float(df["close"].iloc[-1]) if not df.empty else 30_000.0
            return self._flat_result(last, days)

        close = df["close"].values.astype(float)
        n = min(self.lookback, len(close))
        window = close[-n:]

        last_price  = float(window[-1])
        mean_price  = float(np.mean(window))
        std_price   = float(np.std(window))
        log_returns = np.diff(np.log(window + 1e-9))

        # Trend: slope of log-returns
        if len(log_returns) > 1:
            x = np.arange(len(log_returns), dtype=float)
            slope = float(np.polyfit(x, log_returns, 1)[0])
        else:
            slope = 0.0

        # EMA-20 for mean-reversion target
        ema20 = float(pd.Series(close).ewm(span=20, adjust=False).mean().iloc[-1])

        # Seed RNG deterministically from last close so results are stable
        rng = random.Random(int(last_price * 100) % (2**31))

        prices: list[float] = []
        current = last_price
        reversion_strength = 0.05   # pull toward EMA per step
        daily_vol = std_price / math.sqrt(max(n, 1)) * 0.7

        for i in range(days):
            # Trend component
            trend = math.exp(slope * (i + 1)) - 1
            # Mean-reversion nudge
            reversion = (ema20 - current) * reversion_strength
            # Noise
            noise = rng.gauss(0, daily_vol * 0.5)
            current = current * (1 + trend) + reversion + noise
            current = max(current, 500.0)   # VN stocks don't go below 500 VND
            prices.append(round(float(current), -1))

        # Direction & confidence
        pct_change = (prices[-1] - last_price) / last_price if last_price else 0
        direction  = "up" if pct_change > 0 else "down"
        raw_conf   = min(abs(pct_change) * 10 + 0.50, 0.92)
        confidence = round(raw_conf, 2)

        return {
            "prices":     prices,
            "direction":  direction,
            "confidence": confidence,
            "model":      "LSTM (statistical approximation)",
        }

    # ------------------------------------------------------------------
    @staticmethod
    def _flat_result(last: float, days: int) -> dict[str, Any]:
        return {
            "prices":     [round(last, -1)] * days,
            "direction":  "hold",
            "confidence": 0.50,
            "model":      "LSTM (flat – insufficient data)",
        }
