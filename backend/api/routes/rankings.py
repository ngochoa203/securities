"""
Rankings Routes
===============
GET /api/rankings/top-buy       – Strongest Buy signals
GET /api/rankings/top-decline   – Biggest recent decliners
GET /api/rankings/trustworthy   – Blue-chip large-caps
GET /api/rankings/top-invest    – AI-recommended picks
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from services.rankings import (
    get_top_buy,
    get_top_decline,
    get_trustworthy,
    get_top_invest,
)

router = APIRouter(prefix="/api/rankings", tags=["rankings"])


# ---------------------------------------------------------------------------
# GET /api/rankings/top-buy
# ---------------------------------------------------------------------------

@router.get("/top-buy", summary="Stocks with strongest Buy signals")
async def top_buy(
    limit: int = Query(default=10, ge=1, le=50, description="Number of results"),
) -> dict[str, Any]:
    """
    Returns stocks that technical analysis rates as **Buy**.
    Sorted by signal confidence (highest first).
    """
    stocks = get_top_buy(limit=limit)
    return {
        "category":    "top-buy",
        "title":       "Cổ phiếu có tín hiệu Mua mạnh nhất",
        "description": "Dựa trên phân tích kỹ thuật: RSI, MACD, Bollinger Bands và MA",
        "count":       len(stocks),
        "stocks":      stocks,
    }


# ---------------------------------------------------------------------------
# GET /api/rankings/top-decline
# ---------------------------------------------------------------------------

@router.get("/top-decline", summary="Biggest recent price decliners (buy-the-dip)")
async def top_decline(
    limit: int = Query(default=10, ge=1, le=50, description="Number of results"),
) -> dict[str, Any]:
    """
    Returns stocks with the largest percentage price drops recently.
    Useful for identifying buy-the-dip opportunities.
    """
    stocks = get_top_decline(limit=limit)
    return {
        "category":    "top-decline",
        "title":       "Cổ phiếu giảm giá mạnh nhất",
        "description": "Cơ hội mua đáy – Giá đã giảm đáng kể so với phiên trước",
        "count":       len(stocks),
        "stocks":      stocks,
    }


# ---------------------------------------------------------------------------
# GET /api/rankings/trustworthy
# ---------------------------------------------------------------------------

@router.get("/trustworthy", summary="Blue-chip large-cap stocks")
async def trustworthy(
    limit: int = Query(default=10, ge=1, le=20, description="Number of results"),
) -> dict[str, Any]:
    """
    Returns well-known, large-capitalisation Vietnamese blue-chips
    suitable for long-term investment with lower volatility.
    """
    stocks = get_trustworthy(limit=limit)
    return {
        "category":    "trustworthy",
        "title":       "Cổ phiếu Blue-chip đáng tin cậy",
        "description": "Các công ty vốn hóa lớn, ổn định, phù hợp đầu tư dài hạn",
        "count":       len(stocks),
        "stocks":      stocks,
    }


# ---------------------------------------------------------------------------
# GET /api/rankings/top-invest
# ---------------------------------------------------------------------------

@router.get("/top-invest", summary="AI-recommended investment picks")
async def top_invest(
    limit: int = Query(default=10, ge=1, le=25, description="Number of results"),
) -> dict[str, Any]:
    """
    Returns AI-recommended stocks combining technical signal strength
    with ensemble model prediction direction and confidence.
    """
    stocks = get_top_invest(limit=limit)
    return {
        "category":    "top-invest",
        "title":       "AI khuyến nghị đầu tư",
        "description": "Kết hợp phân tích kỹ thuật và mô hình AI dự báo giá",
        "count":       len(stocks),
        "stocks":      stocks,
    }
