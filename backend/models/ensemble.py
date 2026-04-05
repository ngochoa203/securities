"""
Ensemble Predictor
==================
Combines LSTM (40%) + XGBoost (35%) + Prophet (25%) predictions
via weighted average, then derives a unified direction & confidence.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from models.lstm_model import LSTMPredictor
from models.xgboost_model import XGBoostPredictor
from models.prophet_model import ProphetPredictor
from services.stock_data import get_stock_history, get_stock_info


_WEIGHTS = {
    "lstm":    0.40,
    "xgboost": 0.35,
    "prophet": 0.25,
}


class EnsemblePredictor:
    """
    Orchestrates the three sub-models and merges their forecasts.
    """

    def __init__(self):
        self._lstm    = LSTMPredictor()
        self._xgb     = XGBoostPredictor()
        self._prophet = ProphetPredictor()

    # ------------------------------------------------------------------
    def predict(
        self,
        symbol: str,
        period: str = "1y",
        forecast_days: int = 7,
    ) -> dict[str, Any]:
        """
        Full prediction pipeline for a symbol.

        Returns
        -------
        {
            "symbol":        str,
            "current_price": float,
            "predictions":   {"1": price, "7": price, "30": price},
            "direction":     "up" | "down",
            "confidence":    float,
            "model_details": {lstm: {...}, xgboost: {...}, prophet: {...}},
        }
        """
        symbol = symbol.upper()

        # Fetch history
        history = get_stock_history(symbol, period=period)
        df = pd.DataFrame(history)
        if df.empty:
            return self._error_result(symbol)

        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df.dropna(subset=["close"])
        current_price = float(df["close"].iloc[-1])

        # Run sub-models
        lstm_res = self._lstm.predict(df, days=max(forecast_days, 30))
        xgb_res  = self._xgb.predict(df, days=max(forecast_days, 30))
        proph_res = self._prophet.predict(df, days=max(forecast_days, 30))

        def safe_price(res: dict, idx: int) -> float:
            prices = res.get("prices", [])
            if idx < len(prices):
                return float(prices[idx])
            return float(prices[-1]) if prices else current_price

        # Blend at day 1, 7, 30
        def blend(day_idx: int) -> float:
            return round(
                _WEIGHTS["lstm"]    * safe_price(lstm_res,  day_idx) +
                _WEIGHTS["xgboost"] * safe_price(xgb_res,   day_idx) +
                _WEIGHTS["prophet"] * safe_price(proph_res, day_idx),
                -1,
            )

        pred_1  = blend(0)
        pred_7  = blend(min(6, max(forecast_days, 30) - 1))
        pred_30 = blend(min(29, max(forecast_days, 30) - 1))

        # Overall direction and confidence (weighted vote)
        def dir_score(res: dict) -> float:
            """+1 for up, -1 for down, scaled by confidence."""
            d = 1.0 if res.get("direction", "up") == "up" else -1.0
            return d * float(res.get("confidence", 0.5))

        ensemble_score = (
            _WEIGHTS["lstm"]    * dir_score(lstm_res) +
            _WEIGHTS["xgboost"] * dir_score(xgb_res) +
            _WEIGHTS["prophet"] * dir_score(proph_res)
        )
        direction  = "up" if ensemble_score >= 0 else "down"
        confidence = round(min(abs(ensemble_score) + 0.45, 0.95), 2)

        return {
            "symbol":        symbol,
            "current_price": current_price,
            "predictions": {
                "1":  pred_1,
                "7":  pred_7,
                "30": pred_30,
            },
            "direction":  direction,
            "confidence": confidence,
            "model_details": {
                "lstm": {
                    "direction":  lstm_res.get("direction"),
                    "confidence": lstm_res.get("confidence"),
                    "model":      lstm_res.get("model"),
                    "weight":     _WEIGHTS["lstm"],
                },
                "xgboost": {
                    "direction":  xgb_res.get("direction"),
                    "confidence": xgb_res.get("confidence"),
                    "model":      xgb_res.get("model"),
                    "weight":     _WEIGHTS["xgboost"],
                },
                "prophet": {
                    "direction":  proph_res.get("direction"),
                    "confidence": proph_res.get("confidence"),
                    "model":      proph_res.get("model"),
                    "weight":     _WEIGHTS["prophet"],
                },
            },
        }

    # ------------------------------------------------------------------
    @staticmethod
    def _error_result(symbol: str) -> dict[str, Any]:
        return {
            "symbol":        symbol,
            "current_price": 0.0,
            "predictions":   {"1": 0, "7": 0, "30": 0},
            "direction":     "unknown",
            "confidence":    0.0,
            "model_details": {},
        }
