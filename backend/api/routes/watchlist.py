"""
Watchlist, Alerts, and Poller API Routes
=========================================
Provides REST endpoints for managing the realtime price watchlist,
viewing alert history, testing Discord notifications, and checking
poller status.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.realtime_poller import (
    get_watchlist,
    add_to_watchlist,
    remove_from_watchlist,
    get_alert_history,
    get_poller_status,
)
from services.stock_data import get_stock_info, get_realtime_prices
from services import discord_notifier

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

router        = APIRouter(prefix="/api/watchlist", tags=["watchlist"])
alerts_router = APIRouter(prefix="/api/alerts",   tags=["alerts"])
poller_router = APIRouter(prefix="/api/poller",   tags=["poller"])


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class WatchlistAddRequest(BaseModel):
    symbol:     str
    target_low:  float = 0.0
    target_high: float = 0.0


class WatchlistEntry(BaseModel):
    symbol:        str
    target_low:    float
    target_high:   float
    current_price: float | None = None
    prev_close:    float | None = None
    change_pct:    float | None = None


# ---------------------------------------------------------------------------
# Watchlist endpoints
# ---------------------------------------------------------------------------

@router.get("", summary="Lấy danh sách theo dõi")
async def list_watchlist():
    """
    Trả về danh sách theo dõi hiện tại cùng với giá cổ phiếu mới nhất.
    Nếu poller chưa cập nhật giá (ngoài giờ giao dịch), fetch trực tiếp từ DNSE.
    """
    watchlist = get_watchlist()

    # Collect symbols that don't have a price yet
    missing = [w["symbol"] for w in watchlist if not w.get("current_price")]

    if missing:
        # Fetch live prices from DNSE for items without a cached price
        prices = get_realtime_prices(missing)
        for item in watchlist:
            sym = item["symbol"]
            if not item.get("current_price") and sym in prices:
                p = prices[sym]
                item["current_price"] = p["price"]
                item["change_pct"] = p["change_pct"]
                item["prev_close"] = round(p["price"] - p["change"], -1) if p.get("change") else None

    # Also enrich with stock name
    for item in watchlist:
        if not item.get("name"):
            try:
                info = get_stock_info(item["symbol"])
                item["name"] = info.get("name", item["symbol"])
            except Exception:
                item["name"] = item["symbol"]

    return {
        "watchlist": watchlist,
        "count":     len(watchlist),
    }


@router.post("", summary="Thêm cổ phiếu vào danh sách theo dõi")
async def add_watchlist_item(body: WatchlistAddRequest):
    """
    Thêm một mã cổ phiếu vào danh sách theo dõi.
    Nếu mã đã tồn tại, cập nhật vùng giá mục tiêu.
    """
    symbol = body.symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="Mã cổ phiếu không được để trống.")

    entry = add_to_watchlist(symbol, body.target_low, body.target_high)
    return {
        "message": f"Đã thêm {symbol} vào danh sách theo dõi.",
        "entry":   entry,
    }


@router.delete("/{symbol}", summary="Xóa cổ phiếu khỏi danh sách theo dõi")
async def delete_watchlist_item(symbol: str):
    """
    Xóa một mã cổ phiếu khỏi danh sách theo dõi.
    """
    symbol = symbol.strip().upper()
    removed = remove_from_watchlist(symbol)
    if not removed:
        raise HTTPException(
            status_code=404,
            detail=f"Không tìm thấy {symbol} trong danh sách theo dõi.",
        )
    return {"message": f"Đã xóa {symbol} khỏi danh sách theo dõi."}


# ---------------------------------------------------------------------------
# Alerts endpoints
# ---------------------------------------------------------------------------

@alerts_router.get("/history", summary="Lịch sử cảnh báo")
async def get_alerts_history(limit: int = 50):
    """
    Trả về lịch sử cảnh báo gần đây (mặc định 50 bản ghi, tối đa 200).
    """
    if limit < 1:
        limit = 1
    if limit > 200:
        limit = 200
    history = get_alert_history(limit)
    return {
        "alerts": history,
        "count":  len(history),
    }


@alerts_router.post("/test", summary="Gửi thông báo thử nghiệm tới Discord")
async def test_discord_notification():
    """
    Gửi một thông báo thử nghiệm tới Discord để kiểm tra kết nối webhook.
    """
    if not discord_notifier.is_configured():
        raise HTTPException(
            status_code=503,
            detail=(
                "Discord webhook chưa được cấu hình. "
                "Vui lòng đặt biến môi trường DISCORD_WEBHOOK_URL."
            ),
        )

    success = await discord_notifier.send_test_notification()
    if success:
        return {"success": True, "message": "Thông báo thử nghiệm đã được gửi thành công tới Discord."}
    else:
        raise HTTPException(
            status_code=502,
            detail="Không thể gửi thông báo tới Discord. Kiểm tra lại DISCORD_WEBHOOK_URL.",
        )


# ---------------------------------------------------------------------------
# Poller status endpoint
# ---------------------------------------------------------------------------

@poller_router.get("/status", summary="Trạng thái bộ theo dõi giá")
async def poller_status():
    """
    Trả về trạng thái hiện tại của bộ theo dõi giá realtime:
    - running: poller có đang chạy không
    - market_hours: có đang trong giờ giao dịch không
    - last_poll_time: thời điểm poll lần cuối
    - watchlist_count: số mã đang theo dõi
    """
    return get_poller_status()
