"""
Discord Webhook Notifier
========================
Sends rich embed notifications to Discord via webhook URL.
Supports: price alerts, signal changes, good price alerts, session summaries.
"""
import os
import logging
import time
from datetime import datetime
from typing import Any

import httpx

logger = logging.getLogger("securities.discord")

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

# Embed colors
COLOR_GREEN  = 0x2ecc71
COLOR_RED    = 0xe74c3c
COLOR_BLUE   = 0x3498db
COLOR_YELLOW = 0xf1c40f

# Rate limiting: max 1 notification per symbol per 5 minutes
_rate_limit: dict[str, float] = {}
RATE_LIMIT_SECONDS = 300


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_configured() -> bool:
    """Return True if DISCORD_WEBHOOK_URL is set and non-empty."""
    return bool(WEBHOOK_URL)


def _can_send(key: str) -> bool:
    """Return True if the key has not been sent within the rate-limit window."""
    last = _rate_limit.get(key, 0.0)
    return (time.monotonic() - last) >= RATE_LIMIT_SECONDS


def _mark_sent(key: str) -> None:
    """Record the current time as the last send time for *key*."""
    _rate_limit[key] = time.monotonic()


def _fmt_price(price: float) -> str:
    """Format a VND price with thousands separator."""
    return f"{price:,.0f}đ"


def _fmt_pct(pct: float) -> str:
    """Format a percentage with sign."""
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.2f}%"


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


# ---------------------------------------------------------------------------
# Core webhook sender
# ---------------------------------------------------------------------------

async def send_webhook(embeds: list[dict]) -> bool:
    """
    POST *embeds* to the configured Discord webhook.
    Returns True on HTTP 2xx, False otherwise.
    """
    if not is_configured():
        logger.debug("Discord webhook not configured — skipping send.")
        return False

    payload = {"embeds": embeds}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(WEBHOOK_URL, json=payload)
            if resp.status_code in (200, 204):
                logger.debug("Discord webhook sent successfully (status %s).", resp.status_code)
                return True
            else:
                logger.warning(
                    "Discord webhook returned unexpected status %s: %s",
                    resp.status_code,
                    resp.text[:200],
                )
                return False
    except httpx.HTTPError as exc:
        logger.error("Discord webhook HTTP error: %s", exc)
        return False
    except Exception as exc:
        logger.error("Discord webhook unexpected error: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Typed notification senders
# ---------------------------------------------------------------------------

async def send_price_alert(
    symbol: str,
    name: str,
    price: float,
    change_pct: float,
    prev_close: float,
) -> None:
    """
    Gửi cảnh báo 🚨 Biến động mạnh khi giá cổ phiếu thay đổi đáng kể.
    Màu đỏ nếu giảm, xanh nếu tăng.
    """
    key = f"price_alert:{symbol}"
    if not _can_send(key):
        logger.debug("Rate-limited price alert for %s.", symbol)
        return

    color = COLOR_GREEN if change_pct >= 0 else COLOR_RED
    direction = "tăng 📈" if change_pct >= 0 else "giảm 📉"

    embed = {
        "title": f"🚨 Biến động mạnh: {symbol}",
        "description": (
            f"**{name}** ({symbol}) đang {direction} mạnh so với phiên trước."
        ),
        "color": color,
        "fields": [
            {"name": "Giá hiện tại",   "value": _fmt_price(price),      "inline": True},
            {"name": "Thay đổi",       "value": _fmt_pct(change_pct),   "inline": True},
            {"name": "Giá đóng cửa hôm qua", "value": _fmt_price(prev_close), "inline": True},
        ],
        "timestamp": _now_iso(),
        "footer": {"text": "Securities AI | Dữ liệu DNSE"},
    }

    success = await send_webhook([embed])
    if success:
        _mark_sent(key)


async def send_signal_change(
    symbol: str,
    name: str,
    old_signal: str,
    new_signal: str,
    confidence: float,
    reasons: list[str],
) -> None:
    """
    Gửi thông báo 📊 Tín hiệu mới khi tín hiệu kỹ thuật thay đổi.
    Hiển thị tín hiệu cũ → mới, độ tin cậy, và lý do (tối đa 3).
    """
    key = f"signal_change:{symbol}"
    if not _can_send(key):
        logger.debug("Rate-limited signal change for %s.", symbol)
        return

    signal_color: dict[str, int] = {
        "Buy":  COLOR_GREEN,
        "Sell": COLOR_RED,
        "Hold": COLOR_YELLOW,
    }
    color = signal_color.get(new_signal, COLOR_BLUE)

    top_reasons = reasons[:3]
    reasons_text = "\n".join(f"• {r}" for r in top_reasons) if top_reasons else "Không có lý do cụ thể."

    embed = {
        "title": f"📊 Tín hiệu mới: {symbol}",
        "description": (
            f"**{name}** ({symbol}) vừa thay đổi tín hiệu kỹ thuật."
        ),
        "color": color,
        "fields": [
            {"name": "Tín hiệu cũ",    "value": old_signal,                          "inline": True},
            {"name": "Tín hiệu mới",   "value": f"**{new_signal}**",                 "inline": True},
            {"name": "Độ tin cậy",     "value": f"{confidence * 100:.1f}%",          "inline": True},
            {"name": "Lý do phân tích","value": reasons_text,                         "inline": False},
        ],
        "timestamp": _now_iso(),
        "footer": {"text": "Securities AI | Phân tích kỹ thuật"},
    }

    success = await send_webhook([embed])
    if success:
        _mark_sent(key)


async def send_good_price(
    symbol: str,
    name: str,
    price: float,
    target_low: float,
    target_high: float,
) -> None:
    """
    Gửi cảnh báo 💰 Giá tốt khi giá cổ phiếu vào vùng mục tiêu đã đặt.
    """
    key = f"good_price:{symbol}"
    if not _can_send(key):
        logger.debug("Rate-limited good price alert for %s.", symbol)
        return

    embed = {
        "title": f"💰 Giá tốt: {symbol}",
        "description": (
            f"**{name}** ({symbol}) đang ở trong vùng giá mục tiêu của bạn!"
        ),
        "color": COLOR_GREEN,
        "fields": [
            {"name": "Giá hiện tại",   "value": _fmt_price(price),       "inline": True},
            {"name": "Vùng mục tiêu",  "value": (
                f"{_fmt_price(target_low)} – {_fmt_price(target_high)}"
            ), "inline": True},
        ],
        "timestamp": _now_iso(),
        "footer": {"text": "Securities AI | Danh sách theo dõi"},
    }

    success = await send_webhook([embed])
    if success:
        _mark_sent(key)


async def send_buy_recommendation(
    symbol: str,
    name: str,
    price: float,
    signal: str,
    signal_confidence: float,
    prediction_direction: str,
    pred_confidence: float,
) -> None:
    """
    Gửi khuyến nghị 📈 Mua khi cả tín hiệu kỹ thuật (Buy) và
    AI (up) đều đồng thuận với độ tin cậy > 70%.
    """
    key = f"buy_rec:{symbol}"
    if not _can_send(key):
        logger.debug("Rate-limited buy recommendation for %s.", symbol)
        return

    embed = {
        "title": f"📈 Khuyến nghị mua: {symbol}",
        "description": (
            f"**{name}** ({symbol}) — cả phân tích kỹ thuật và AI đều"
            f" đồng thuận xu hướng tăng với độ tin cậy cao!"
        ),
        "color": COLOR_GREEN,
        "fields": [
            {"name": "Giá hiện tại",        "value": _fmt_price(price),                    "inline": True},
            {"name": "Tín hiệu kỹ thuật",   "value": f"{signal} ({signal_confidence*100:.1f}%)",   "inline": True},
            {"name": "Dự báo AI",            "value": f"{prediction_direction} ({pred_confidence*100:.1f}%)", "inline": True},
            {"name": "⚠️ Lưu ý",            "value": "Đây không phải lời khuyên đầu tư. Hãy tự nghiên cứu thêm.", "inline": False},
        ],
        "timestamp": _now_iso(),
        "footer": {"text": "Securities AI | Tín hiệu tổng hợp"},
    }

    success = await send_webhook([embed])
    if success:
        _mark_sent(key)


async def send_session_summary(stocks: list[dict], market_data: dict) -> None:
    """
    Gửi tổng kết phiên 🔔 lúc 15:00.
    Bao gồm: top tăng, top giảm, thay đổi tín hiệu, tóm tắt VN-Index.
    Rate limit không áp dụng cho tổng kết phiên.
    """
    # Sort by change_pct descending for gainers/losers
    sorted_stocks = sorted(stocks, key=lambda s: s.get("change_pct", 0), reverse=True)
    top_gainers = sorted_stocks[:3]
    top_losers  = sorted_stocks[-3:][::-1]  # worst performers

    def fmt_stock_line(s: dict) -> str:
        sym = s.get("symbol", "?")
        pct = s.get("change_pct", 0.0)
        price = s.get("price", 0.0)
        return f"**{sym}** {_fmt_price(price)} ({_fmt_pct(pct)})"

    gainers_text = "\n".join(fmt_stock_line(s) for s in top_gainers) or "Không có dữ liệu"
    losers_text  = "\n".join(fmt_stock_line(s) for s in top_losers)  or "Không có dữ liệu"

    # Signal changes
    signal_changes = [s for s in stocks if s.get("signal_changed")]
    signals_text = (
        "\n".join(
            f"**{s['symbol']}**: {s.get('old_signal','?')} → {s.get('new_signal','?')}"
            for s in signal_changes[:5]
        )
        or "Không có thay đổi tín hiệu trong phiên."
    )

    vnindex_value = market_data.get("vn_index", "N/A")
    vnindex_change = market_data.get("vn_index_change", 0.0)
    vn_color = COLOR_GREEN if vnindex_change >= 0 else COLOR_RED

    embed = {
        "title": "🔔 Tổng kết phiên giao dịch",
        "description": (
            f"Kết thúc phiên giao dịch. "
            f"VN-Index: **{vnindex_value}** ({_fmt_pct(vnindex_change)})"
        ),
        "color": vn_color,
        "fields": [
            {"name": "🏆 Top tăng mạnh",      "value": gainers_text, "inline": True},
            {"name": "📉 Top giảm mạnh",       "value": losers_text,  "inline": True},
            {"name": "📊 Thay đổi tín hiệu",   "value": signals_text, "inline": False},
        ],
        "timestamp": _now_iso(),
        "footer": {"text": "Securities AI | Tổng kết phiên"},
    }

    await send_webhook([embed])


async def send_test_notification() -> bool:
    """
    Gửi thông báo thử nghiệm để kiểm tra webhook có hoạt động không.
    Trả về True nếu thành công.
    """
    embed = {
        "title": "✅ Kiểm tra kết nối Discord",
        "description": (
            "Webhook Discord đã được kết nối thành công với **Securities AI**!\n"
            "Bạn sẽ nhận được thông báo về biến động giá, tín hiệu kỹ thuật, "
            "và khuyến nghị đầu tư tại đây."
        ),
        "color": COLOR_BLUE,
        "fields": [
            {"name": "Trạng thái",  "value": "🟢 Hoạt động",     "inline": True},
            {"name": "Thời gian",   "value": datetime.now().strftime("%H:%M %d/%m/%Y"), "inline": True},
        ],
        "timestamp": _now_iso(),
        "footer": {"text": "Securities AI | Kiểm tra hệ thống"},
    }
    return await send_webhook([embed])


async def send_priority_stock_report(
    symbol: str,
    name: str,
    price: float,
    change: float,
    change_pct: float,
    prev_close: float,
    high_30d: float,
    low_30d: float,
    rsi: float | None,
    signal: str,
    signal_confidence: float,
    macd_status: str,
    prediction_1d: float,
    prediction_7d: float,
    prediction_30d: float,
    pred_direction: str,
    pred_confidence: float,
    reasons: list[str],
) -> None:
    """
    Gửi báo cáo phân tích chi tiết ⭐ cho cổ phiếu ưu tiên (VCB, MBB).
    Bao gồm: giá, kỹ thuật, dự đoán AI, hành động khuyến nghị.
    Không áp dụng rate limit.
    """
    color = COLOR_GREEN if change_pct >= 0 else COLOR_RED
    direction_emoji = "📈" if change_pct >= 0 else "📉"
    pred_emoji = "🔼" if pred_direction == "up" else "🔽"

    signal_emoji_map = {"Buy": "🟢 MUA", "Sell": "🔴 BÁN", "Hold": "🟡 GIỮ"}
    signal_display = signal_emoji_map.get(signal, f"⚪ {signal}")

    rsi_text = f"{rsi:.1f}" if rsi is not None else "N/A"
    rsi_status = ""
    if rsi is not None:
        if rsi < 30:
            rsi_status = " (Quá bán ⚡)"
        elif rsi > 70:
            rsi_status = " (Quá mua ⚠️)"
        elif rsi < 45:
            rsi_status = " (Vùng tích lũy)"
        else:
            rsi_status = " (Bình thường)"

    reasons_text = "\n".join(f"• {r}" for r in reasons[:4]) if reasons else "Không có lý do cụ thể"

    # Position in 30-day range (0% = at low, 100% = at high)
    range_span = high_30d - low_30d if high_30d > low_30d else 1
    range_pct = ((price - low_30d) / range_span) * 100
    range_bar_len = 10
    filled = int(range_pct / 100 * range_bar_len)
    range_bar = "█" * filled + "░" * (range_bar_len - filled)

    embed = {
        "title": f"⭐ Báo cáo chi tiết: {symbol} — {name}",
        "description": (
            f"{direction_emoji} **{symbol}** đang giao dịch ở **{_fmt_price(price)}** "
            f"({_fmt_pct(change_pct)} so với hôm qua)\n"
            f"Đây là cổ phiếu bạn đang **theo dõi đặc biệt**."
        ),
        "color": color,
        "fields": [
            {"name": "💵 Giá hiện tại", "value": _fmt_price(price), "inline": True},
            {"name": "📊 Thay đổi", "value": f"{_fmt_price(change)} ({_fmt_pct(change_pct)})", "inline": True},
            {"name": "📍 Giá hôm qua", "value": _fmt_price(prev_close), "inline": True},

            {"name": "📏 Biên độ 30 ngày", "value": f"{_fmt_price(low_30d)} — {_fmt_price(high_30d)}\n`[{range_bar}]` {range_pct:.0f}%", "inline": False},

            {"name": "🎯 Tín hiệu kỹ thuật", "value": f"{signal_display}\nĐộ tin cậy: **{signal_confidence*100:.0f}%**", "inline": True},
            {"name": "📉 RSI", "value": f"{rsi_text}{rsi_status}", "inline": True},
            {"name": "📊 MACD", "value": macd_status, "inline": True},

            {"name": f"{pred_emoji} Dự đoán AI", "value": (
                f"1 ngày: **{_fmt_price(prediction_1d)}**\n"
                f"7 ngày: **{_fmt_price(prediction_7d)}**\n"
                f"30 ngày: **{_fmt_price(prediction_30d)}**\n"
                f"Hướng: **{pred_direction.upper()}** ({pred_confidence*100:.0f}%)"
            ), "inline": False},

            {"name": "📋 Phân tích", "value": reasons_text, "inline": False},

            {"name": "⚠️ Lưu ý", "value": "Đây không phải lời khuyên đầu tư. Hãy tự nghiên cứu thêm trước khi quyết định.", "inline": False},
        ],
        "timestamp": _now_iso(),
        "footer": {"text": "Securities AI | Theo dõi đặc biệt | Dữ liệu DNSE"},
    }

    await send_webhook([embed])
