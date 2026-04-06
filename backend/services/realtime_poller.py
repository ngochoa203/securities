"""
Realtime Price Poller
=====================
Background asyncio task that polls DNSE every 60s during market hours.
Detects price movements, signal changes, and watchlist alerts.
Sends notifications via Discord webhook.
"""
import asyncio
import logging
from datetime import datetime, time as dt_time, timezone, timedelta
from typing import Any

import pandas as pd

from services.stock_data import _fetch_dnse_history, get_stock_info, VN_STOCKS
from services.technical import calculate_all_indicators, generate_signal
from services import discord_notifier

logger = logging.getLogger("securities.poller")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Vietnam timezone offset: UTC+7
_TZ_VN = timezone(timedelta(hours=7))

# Market hours in VN local time
MARKET_OPEN_MORNING   = dt_time(9,  0)
MARKET_CLOSE_MORNING  = dt_time(11, 30)
MARKET_OPEN_AFTERNOON = dt_time(13, 0)
MARKET_CLOSE_AFTERNOON = dt_time(15, 0)
SESSION_SUMMARY_TIME   = dt_time(15, 5)

POLL_INTERVAL = 60  # seconds

# Default top-10 most-traded VN stocks
DEFAULT_WATCHLIST = ["FPT", "VNM", "VIC", "HPG", "TCB", "VCB", "MWG", "MBB", "ACB", "VPB"]

# ── Priority stocks: lower alert threshold, more detailed Discord reports ──
PRIORITY_STOCKS: dict[str, dict] = {
    "VCB": {"name": "Vietcombank", "alert_threshold": 1.5, "track_intraday": True},
    "MBB": {"name": "MB Bank",    "alert_threshold": 1.5, "track_intraday": True},
}

# Alert thresholds
PRICE_ALERT_THRESHOLD  = 3.0   # % change from prev close to trigger alert (normal stocks)
PRIORITY_ALERT_THRESHOLD = 1.5 # % change for priority stocks (VCB, MBB)
BUY_CONFIDENCE_THRESHOLD = 0.70  # min confidence for buy recommendation

_MAX_ALERT_HISTORY = 200

# ---------------------------------------------------------------------------
# In-memory state
# ---------------------------------------------------------------------------

_watchlist: list[dict] = []           # [{"symbol": "FPT", "target_low": 0, "target_high": 0}, ...]
_previous_signals: dict[str, str] = {}  # symbol -> last known signal
_session_open_prices: dict[str, float] = {}  # symbol -> price at session open
_alert_history: list[dict] = []       # recent alerts
_poller_task: asyncio.Task | None = None
_poller_running: bool = False
_last_poll_time: datetime | None = None
_summary_sent_today: str = ""         # date string "YYYY-MM-DD" to avoid duplicate summaries


# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------

def _now_vn() -> datetime:
    """Return current datetime in Vietnam timezone (UTC+7)."""
    return datetime.now(_TZ_VN)


def is_market_hours() -> bool:
    """Return True if current VN time falls within trading sessions."""
    now_time = _now_vn().time()
    morning   = MARKET_OPEN_MORNING   <= now_time <= MARKET_CLOSE_MORNING
    afternoon = MARKET_OPEN_AFTERNOON <= now_time <= MARKET_CLOSE_AFTERNOON
    return morning or afternoon


def _is_summary_time() -> bool:
    """Return True if it is time to send the session summary (15:05)."""
    now_time = _now_vn().time()
    return (
        SESSION_SUMMARY_TIME <= now_time <= dt_time(15, 10)
        and _now_vn().strftime("%Y-%m-%d") != _summary_sent_today
    )


# ---------------------------------------------------------------------------
# Watchlist management
# ---------------------------------------------------------------------------

def get_watchlist() -> list[dict]:
    """Return a shallow copy of the current watchlist."""
    return list(_watchlist)


def add_to_watchlist(symbol: str, target_low: float = 0.0, target_high: float = 0.0) -> dict:
    """
    Add *symbol* to the watchlist.
    If already present, update target prices.
    Returns the watchlist entry.
    """
    symbol = symbol.upper()
    for entry in _watchlist:
        if entry["symbol"] == symbol:
            entry["target_low"]  = target_low
            entry["target_high"] = target_high
            logger.info("Updated watchlist entry for %s.", symbol)
            return entry

    entry = {
        "symbol":      symbol,
        "target_low":  target_low,
        "target_high": target_high,
        "current_price": None,
        "prev_close":    None,
        "change_pct":    None,
    }
    _watchlist.append(entry)
    logger.info("Added %s to watchlist (total: %d).", symbol, len(_watchlist))
    return entry


def remove_from_watchlist(symbol: str) -> bool:
    """Remove *symbol* from the watchlist. Returns True if found and removed."""
    symbol = symbol.upper()
    global _watchlist
    before = len(_watchlist)
    _watchlist = [e for e in _watchlist if e["symbol"] != symbol]
    removed = len(_watchlist) < before
    if removed:
        logger.info("Removed %s from watchlist.", symbol)
    return removed


# ---------------------------------------------------------------------------
# Alert history
# ---------------------------------------------------------------------------

def get_alert_history(limit: int = 50) -> list[dict]:
    """Return the most recent *limit* alerts (newest first)."""
    return list(reversed(_alert_history))[:limit]


def _add_alert(alert_type: str, symbol: str, message: str, data: dict) -> None:
    """Append an alert to history, capped at _MAX_ALERT_HISTORY entries."""
    global _alert_history
    _alert_history.append({
        "type":      alert_type,
        "symbol":    symbol,
        "message":   message,
        "data":      data,
        "timestamp": _now_vn().isoformat(),
    })
    if len(_alert_history) > _MAX_ALERT_HISTORY:
        _alert_history = _alert_history[-_MAX_ALERT_HISTORY:]


# ---------------------------------------------------------------------------
# Price fetching helper
# ---------------------------------------------------------------------------

def _get_latest_price(symbol: str) -> tuple[float | None, float | None]:
    """
    Fetch the latest close price and previous close for *symbol*.
    Returns (current_price, prev_close). Returns (None, None) on error.
    """
    try:
        rows = _fetch_dnse_history(symbol, days=5)
        if not rows or len(rows) < 2:
            return None, None
        # rows are sorted ascending by date
        current = float(rows[-1]["close"])
        prev    = float(rows[-2]["close"])
        return current, prev
    except Exception as exc:
        logger.warning("Failed to fetch price for %s: %s", symbol, exc)
        return None, None


def _get_stock_name(symbol: str) -> str:
    """Return the display name for a symbol, falling back to the symbol itself."""
    try:
        info = get_stock_info(symbol)
        return info.get("name", symbol) if info else symbol
    except Exception:
        return symbol


# ---------------------------------------------------------------------------
# Per-symbol check routines
# ---------------------------------------------------------------------------

async def _check_price_alerts(symbol: str, current_price: float, prev_close: float) -> None:
    """Send a price alert if the price moved beyond the threshold.
    Priority stocks (VCB, MBB) use a lower threshold (1.5%) for closer monitoring."""
    if prev_close <= 0:
        return
    change_pct = ((current_price - prev_close) / prev_close) * 100
    threshold = PRIORITY_STOCKS[symbol]["alert_threshold"] if symbol in PRIORITY_STOCKS else PRICE_ALERT_THRESHOLD
    if abs(change_pct) >= threshold:
        name = _get_stock_name(symbol)
        is_priority = symbol in PRIORITY_STOCKS
        priority_tag = " ⭐ THEO DÕI ĐẶC BIỆT" if is_priority else ""
        logger.info(
            "Price alert for %s%s: %.2f%% change (%.0f -> %.0f)",
            symbol, priority_tag, change_pct, prev_close, current_price,
        )
        _add_alert(
            "price_alert", symbol,
            f"{symbol}{priority_tag} biến động {change_pct:+.2f}%",
            {"price": current_price, "prev_close": prev_close, "change_pct": change_pct, "priority": is_priority},
        )
        await discord_notifier.send_price_alert(symbol, name, current_price, change_pct, prev_close)


async def _check_signal_change(symbol: str, name: str) -> dict | None:
    """
    Fetch recent OHLCV, compute technical indicators, and compare with the
    previously cached signal. Sends a Discord notification on change.
    Returns a dict with signal info (used for session summary), or None on error.
    """
    try:
        rows = _fetch_dnse_history(symbol, days=60)
        if not rows or len(rows) < 20:
            return None

        df = pd.DataFrame(rows)
        df["time"] = pd.to_datetime(df["time"])
        df.set_index("time", inplace=True)
        df = df.astype({col: float for col in ["open", "high", "low", "close", "volume"]})

        indicators = calculate_all_indicators(df)
        result     = generate_signal(indicators)

        signal     = result.get("signal", "Hold")
        confidence = float(result.get("confidence", 0.0))
        reasons    = result.get("reasons", [])

        prev_signal = _previous_signals.get(symbol)
        _previous_signals[symbol] = signal

        if prev_signal is not None and prev_signal != signal:
            logger.info("Signal change for %s: %s → %s (%.1f%%)", symbol, prev_signal, signal, confidence * 100)
            _add_alert(
                "signal_change", symbol,
                f"{symbol}: {prev_signal} → {signal}",
                {"old_signal": prev_signal, "new_signal": signal, "confidence": confidence},
            )
            await discord_notifier.send_signal_change(symbol, name, prev_signal, signal, confidence, reasons)

        return {
            "symbol":      symbol,
            "signal":      signal,
            "confidence":  confidence,
            "old_signal":  prev_signal,
            "signal_changed": prev_signal is not None and prev_signal != signal,
        }
    except Exception as exc:
        logger.warning("Signal check failed for %s: %s", symbol, exc)
        return None


async def _check_watchlist_targets(symbol: str, current_price: float, name: str) -> None:
    """Send a good-price alert if the current price is within the symbol's target range."""
    entry = next((e for e in _watchlist if e["symbol"] == symbol), None)
    if not entry:
        return

    target_low  = entry.get("target_low",  0.0)
    target_high = entry.get("target_high", 0.0)

    if target_low <= 0 and target_high <= 0:
        return  # no target set

    in_range = (target_low <= current_price <= target_high) if target_high > 0 else (current_price >= target_low)
    if in_range:
        logger.info("Good price alert for %s at %.0f (target %.0f–%.0f).", symbol, current_price, target_low, target_high)
        _add_alert(
            "good_price", symbol,
            f"{symbol} vào vùng giá mục tiêu: {current_price:,.0f}đ",
            {"price": current_price, "target_low": target_low, "target_high": target_high},
        )
        await discord_notifier.send_good_price(symbol, name, current_price, target_low, target_high)


async def _check_buy_recommendation(symbol: str, name: str) -> None:
    """
    Send a buy recommendation when:
    - Technical signal is 'Buy' with confidence >= BUY_CONFIDENCE_THRESHOLD
    - AI prediction direction is 'up' with confidence >= BUY_CONFIDENCE_THRESHOLD
    """
    try:
        # Technical signal
        tech_result = None
        rows = _fetch_dnse_history(symbol, days=60)
        if rows and len(rows) >= 20:
            df = pd.DataFrame(rows)
            df["time"] = pd.to_datetime(df["time"])
            df.set_index("time", inplace=True)
            df = df.astype({col: float for col in ["open", "high", "low", "close", "volume"]})
            indicators  = calculate_all_indicators(df)
            tech_result = generate_signal(indicators)

        if not tech_result:
            return

        tech_signal = tech_result.get("signal", "Hold")
        tech_conf   = float(tech_result.get("confidence", 0.0))

        if tech_signal != "Buy" or tech_conf < BUY_CONFIDENCE_THRESHOLD:
            return

        # AI prediction
        try:
            from models.ensemble import EnsemblePredictor  # noqa: PLC0415
            ai_result  = EnsemblePredictor.predict(symbol)
            ai_dir     = ai_result.get("direction", "")
            ai_conf    = float(ai_result.get("confidence", 0.0))
        except Exception as exc:
            logger.debug("AI prediction unavailable for %s: %s", symbol, exc)
            return

        if ai_dir != "up" or ai_conf < BUY_CONFIDENCE_THRESHOLD:
            return

        current_price, _ = _get_latest_price(symbol)
        if not current_price:
            return

        logger.info(
            "Buy recommendation for %s: tech=%s(%.1f%%) ai=%s(%.1f%%)",
            symbol, tech_signal, tech_conf * 100, ai_dir, ai_conf * 100,
        )
        _add_alert(
            "buy_recommendation", symbol,
            f"Khuyến nghị mua {symbol}: kỹ thuật={tech_signal}, AI={ai_dir}",
            {"price": current_price, "tech_signal": tech_signal, "tech_conf": tech_conf,
             "ai_direction": ai_dir, "ai_conf": ai_conf},
        )
        await discord_notifier.send_buy_recommendation(
            symbol, name, current_price, tech_signal, tech_conf, ai_dir, ai_conf,
        )
    except Exception as exc:
        logger.warning("Buy recommendation check failed for %s: %s", symbol, exc)


# ---------------------------------------------------------------------------
# Poll cycle
# ---------------------------------------------------------------------------

async def _poll_cycle() -> list[dict]:
    """
    One full polling cycle:
    1. Fetch prices for all watchlist symbols.
    2. Update watchlist entries with current prices.
    3. Run all alert checks concurrently per symbol.
    Returns a list of stock state dicts for the session summary.
    """
    global _last_poll_time
    _last_poll_time = _now_vn()

    symbols = [e["symbol"] for e in _watchlist]
    if not symbols:
        logger.debug("Watchlist is empty — skipping poll cycle.")
        return []

    logger.info("🔄 Poll cycle started for %d symbols.", len(symbols))

    stock_states: list[dict] = []

    for symbol in symbols:
        try:
            current_price, prev_close = _get_latest_price(symbol)
            if current_price is None:
                continue

            # Update in-memory entry
            for entry in _watchlist:
                if entry["symbol"] == symbol:
                    entry["current_price"] = current_price
                    entry["prev_close"]    = prev_close
                    if prev_close and prev_close > 0:
                        entry["change_pct"] = ((current_price - prev_close) / prev_close) * 100
                    break

            name = _get_stock_name(symbol)

            # Run checks concurrently
            signal_info, *_ = await asyncio.gather(
                _check_signal_change(symbol, name),
                _check_price_alerts(symbol, current_price, prev_close or 0),
                _check_watchlist_targets(symbol, current_price, name),
                _check_buy_recommendation(symbol, name),
                return_exceptions=True,
            )

            state: dict[str, Any] = {
                "symbol":      symbol,
                "name":        name,
                "price":       current_price,
                "prev_close":  prev_close,
                "change_pct":  ((current_price - (prev_close or current_price)) / (prev_close or current_price)) * 100,
            }
            if isinstance(signal_info, dict):
                state.update(signal_info)

            stock_states.append(state)

        except Exception as exc:
            logger.error("Unexpected error polling %s: %s", symbol, exc)

    logger.info("✅ Poll cycle complete (%d symbols processed).", len(stock_states))
    return stock_states


# ---------------------------------------------------------------------------
# Session summary
# ---------------------------------------------------------------------------

async def _send_session_summary() -> None:
    """Build and send the end-of-day summary to Discord."""
    global _summary_sent_today

    logger.info("📋 Sending session summary…")
    try:
        symbols = [e["symbol"] for e in _watchlist]
        stock_states: list[dict] = []

        for symbol in symbols:
            entry = next((e for e in _watchlist if e["symbol"] == symbol), {})
            stock_states.append({
                "symbol":        symbol,
                "price":         entry.get("current_price", 0),
                "change_pct":    entry.get("change_pct", 0),
                "signal_changed": False,
                "old_signal":    _previous_signals.get(symbol, "Hold"),
                "new_signal":    _previous_signals.get(symbol, "Hold"),
            })

        # Placeholder market data — replace with real VN-Index fetch if available
        market_data = {
            "vn_index":        "N/A",
            "vn_index_change": 0.0,
        }
        try:
            from services.stock_data import get_market_overview  # noqa: PLC0415
            overview = get_market_overview()
            if overview:
                market_data["vn_index"]        = overview.get("vn_index", "N/A")
                market_data["vn_index_change"] = float(overview.get("vn_index_change", 0.0))
        except Exception as exc:
            logger.debug("Could not fetch market overview for summary: %s", exc)

        await discord_notifier.send_session_summary(stock_states, market_data)
        _summary_sent_today = _now_vn().strftime("%Y-%m-%d")
        logger.info("✅ Session summary sent.")
    except Exception as exc:
        logger.error("Failed to send session summary: %s", exc)


# ---------------------------------------------------------------------------
# Main poller loop
# ---------------------------------------------------------------------------

async def poller_loop() -> None:
    """
    Main background loop.
    - During market hours: poll every POLL_INTERVAL seconds.
    - Outside market hours: sleep 60s and re-check.
    - At SESSION_SUMMARY_TIME: send end-of-day summary.
    """
    global _poller_running
    logger.info("🟢 Poller loop started.")

    while _poller_running:
        try:
            in_market = is_market_hours()

            if _is_summary_time():
                await _send_session_summary()

            if in_market:
                await _poll_cycle()
                await asyncio.sleep(POLL_INTERVAL)
            else:
                logger.debug("Outside market hours — poller idle.")
                await asyncio.sleep(60)

        except asyncio.CancelledError:
            logger.info("Poller loop cancelled.")
            break
        except Exception as exc:
            logger.error("Unexpected error in poller loop: %s", exc)
            await asyncio.sleep(60)  # back-off before retrying

    logger.info("🔴 Poller loop exited.")


# ---------------------------------------------------------------------------
# Public lifecycle API
# ---------------------------------------------------------------------------

async def start_poller() -> None:
    """Initialize watchlist with DEFAULT_WATCHLIST and start the background polling task."""
    global _poller_task, _poller_running

    # Populate watchlist with defaults (don't overwrite existing entries)
    existing_symbols = {e["symbol"] for e in _watchlist}
    for sym in DEFAULT_WATCHLIST:
        if sym not in existing_symbols:
            add_to_watchlist(sym)

    if _poller_task and not _poller_task.done():
        logger.warning("Poller is already running.")
        return

    _poller_running = True
    _poller_task = asyncio.create_task(poller_loop(), name="realtime-poller")
    logger.info("🚀 Realtime poller started (watching %d symbols).", len(_watchlist))


async def stop_poller() -> None:
    """Gracefully stop the background polling task."""
    global _poller_running, _poller_task

    _poller_running = False

    if _poller_task and not _poller_task.done():
        _poller_task.cancel()
        try:
            await asyncio.wait_for(_poller_task, timeout=5.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass

    _poller_task = None
    logger.info("🛑 Realtime poller stopped.")


def get_poller_status() -> dict:
    """Return a status snapshot of the poller for the API."""
    from services.discord_notifier import is_configured as discord_is_configured
    return {
        "running":            _poller_running and (_poller_task is not None and not _poller_task.done()),
        "market_hours":       is_market_hours(),
        "last_poll_time":     _last_poll_time.isoformat() if _last_poll_time else None,
        "watchlist_count":    len(_watchlist),
        "discord_configured": discord_is_configured(),
    }
