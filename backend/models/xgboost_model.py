"""
XGBoost Predictor
=================
Feature-engineers returns / technical indicators from OHLCV data,
fits a lightweight XGBoost regressor on the historical data itself,
then predicts the next `days` closing prices.

Falls back to a statistical drift model if XGBoost is unavailable.
"""

from __future__ import annotations

import math
import random
from typing import Any

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------

def _build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create lagged & technical features for supervised learning."""
    df = df.copy()
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["close"])

    c = df["close"]

    # Log returns
    df["ret_1"]  = c.pct_change(1)
    df["ret_3"]  = c.pct_change(3)
    df["ret_5"]  = c.pct_change(5)
    df["ret_10"] = c.pct_change(10)

    # Moving averages and distance from them
    df["sma5"]   = c.rolling(5).mean()
    df["sma20"]  = c.rolling(20).mean()
    df["ema12"]  = c.ewm(span=12, adjust=False).mean()
    df["dist_sma5"]  = (c - df["sma5"]) / df["sma5"]
    df["dist_sma20"] = (c - df["sma20"]) / df["sma20"]

    # Volatility
    df["vol5"]  = c.rolling(5).std()
    df["vol20"] = c.rolling(20).std()

    # Volume if available
    if "volume" in df.columns:
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0)
        df["vol_ret"] = df["volume"].pct_change(1)
    else:
        df["vol_ret"] = 0.0

    # Lagged closes (as fraction of current close)
    for lag in (1, 2, 3, 5, 10):
        df[f"lag_{lag}"] = c.shift(lag) / c

    # Target: next-day close
    df["target"] = c.shift(-1)

    return df.dropna()


# ---------------------------------------------------------------------------
# Statistical fallback
# ---------------------------------------------------------------------------

def _statistical_predict(close: np.ndarray, days: int, seed: int = 42) -> list[float]:
    """Simple drift + volatility extrapolation."""
    log_ret = np.diff(np.log(close + 1e-9))
    mu  = float(np.mean(log_ret[-20:]))
    sig = float(np.std(log_ret[-20:]))
    rng = random.Random(seed)
    current = float(close[-1])
    prices: list[float] = []
    for _ in range(days):
        shock = rng.gauss(mu, sig)
        current = current * math.exp(shock)
        current = max(current, 500.0)
        prices.append(round(float(current), -1))
    return prices


# ---------------------------------------------------------------------------
# Predictor class
# ---------------------------------------------------------------------------

class XGBoostPredictor:
    """
    Fits a small XGBoost regressor on the provided history and
    iteratively predicts future closing prices.
    """

    def __init__(self):
        self._model = None
        self._feature_cols: list[str] = []

    # ------------------------------------------------------------------
    def _fit(self, df_feat: pd.DataFrame) -> bool:
        """Train the model on df_feat.  Returns True on success."""
        try:
            import xgboost as xgb  # noqa: PLC0415
        except (ImportError, Exception):
            return False

        feature_cols = [c for c in df_feat.columns if c not in ("target", "close")]
        X = df_feat[feature_cols].values.astype(float)
        y = df_feat["target"].values.astype(float)

        # Normalise X
        self._x_mean = X.mean(axis=0)
        self._x_std  = X.std(axis=0) + 1e-9
        Xn = (X - self._x_mean) / self._x_std

        model = xgb.XGBRegressor(
            n_estimators=80,
            max_depth=4,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbosity=0,
        )
        model.fit(Xn, y)
        self._model = model
        self._feature_cols = feature_cols
        return True

    # ------------------------------------------------------------------
    def predict(self, df: pd.DataFrame, days: int = 7) -> dict[str, Any]:
        """
        Predict the next `days` closing prices.

        Returns
        -------
        dict with keys: prices, direction, confidence, model
        """
        df = df.copy()
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df.dropna(subset=["close"])
        close_arr = df["close"].values.astype(float)

        if len(df) < 20:
            seed = int(close_arr[-1] * 100) % (2**31) if len(close_arr) else 42
            prices = _statistical_predict(close_arr if len(close_arr) else np.array([30_000.0]), days, seed)
            return self._result(prices, close_arr[-1] if len(close_arr) else prices[0], "XGBoost (fallback – insufficient data)")

        df_feat = _build_features(df)

        if len(df_feat) < 10 or not self._fit(df_feat):
            seed = int(close_arr[-1] * 100) % (2**31)
            prices = _statistical_predict(close_arr, days, seed)
            return self._result(prices, close_arr[-1], "XGBoost (statistical fallback)")

        # Iterative prediction: append each predicted close to rolling window
        rolling_df = df.copy()
        prices: list[float] = []

        for _ in range(days):
            feat_df = _build_features(rolling_df)
            if feat_df.empty:
                break
            last_row = feat_df[self._feature_cols].iloc[[-1]].values.astype(float)
            last_norm = (last_row - self._x_mean) / self._x_std
            pred = float(self._model.predict(last_norm)[0])
            pred = max(pred, 500.0)
            prices.append(round(pred, -1))

            # Append predicted close to rolling window for next step
            new_row = {col: rolling_df[col].iloc[-1] for col in rolling_df.columns}
            new_row["close"] = pred
            rolling_df = pd.concat([rolling_df, pd.DataFrame([new_row])], ignore_index=True)

        if len(prices) < days:
            # Pad with statistical extrapolation
            extra = _statistical_predict(close_arr, days - len(prices))
            prices += extra

        return self._result(prices, float(close_arr[-1]), "XGBoost")

    # ------------------------------------------------------------------
    @staticmethod
    def _result(prices: list[float], last_price: float, model_name: str) -> dict[str, Any]:
        pct = (prices[-1] - last_price) / last_price if last_price else 0
        direction = "up" if pct > 0 else "down"
        confidence = round(min(abs(pct) * 8 + 0.50, 0.92), 2)
        return {
            "prices":     prices,
            "direction":  direction,
            "confidence": confidence,
            "model":      model_name,
        }
