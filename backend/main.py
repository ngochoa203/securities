"""
FastAPI Application Entry Point
================================
Starts the Vietnamese Stock Market Prediction backend.

Run with:
    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s – %(message)s",
)
logger = logging.getLogger("securities.main")


# ---------------------------------------------------------------------------
# Lifespan: pre-warm caches on startup, start/stop poller
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Pre-warm the data caches so the first request is fast.
    Start the realtime price poller on startup and stop it on shutdown.
    """
    logger.info("🚀 Warming up caches…")
    try:
        from services.stock_data import get_stock_list, get_market_overview  # noqa: PLC0415
        get_stock_list()
        get_market_overview()
        logger.info("✅ Cache warm-up complete.")
    except Exception as exc:
        logger.warning("⚠️  Cache warm-up failed (non-critical): %s", exc)

    # Start realtime poller
    logger.info("🔄 Starting realtime price poller…")
    try:
        from services.realtime_poller import start_poller  # noqa: PLC0415
        await start_poller()
    except Exception as exc:
        logger.warning("⚠️  Realtime poller failed to start (non-critical): %s", exc)

    yield

    # Stop poller on shutdown
    logger.info("🛑 Stopping realtime poller…")
    try:
        from services.realtime_poller import stop_poller  # noqa: PLC0415
        await stop_poller()
    except Exception as exc:
        logger.warning("⚠️  Error stopping poller: %s", exc)
    logger.info("🛑 Application shutdown.")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Vietnam Securities AI API",
    description=(
        "Backend for the Vietnamese Stock Market Prediction web application. "
        "Provides real-time (or simulated) OHLCV data, technical analysis, "
        "AI ensemble price predictions, stock rankings, and a Vietnamese "
        "beginner investment guide."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

from api.routes.stocks     import router as stocks_router      # noqa: E402
from api.routes.rankings   import router as rankings_router    # noqa: E402
from api.routes.guide      import router as guide_router       # noqa: E402
from api.routes.watchlist  import router as watchlist_router, alerts_router, poller_router  # noqa: E402

app.include_router(stocks_router)
app.include_router(rankings_router)
app.include_router(guide_router)
app.include_router(watchlist_router)
app.include_router(alerts_router)
app.include_router(poller_router)


# ---------------------------------------------------------------------------
# Health / root
# ---------------------------------------------------------------------------

@app.get("/", tags=["health"], summary="Health check")
async def root():
    """
    Returns API health status and a list of available endpoint groups.
    """
    return {
        "status":  "ok",
        "message": "Vietnam Securities AI API is running",
        "version": "1.0.0",
        "endpoints": {
            "stocks":    "/api/stocks",
            "rankings":  "/api/rankings",
            "guide":     "/api/guide",
            "watchlist": "/api/watchlist",
            "alerts":    "/api/alerts",
            "poller":    "/api/poller",
            "docs":      "/docs",
        },
    }


@app.get("/health", tags=["health"], summary="Detailed health check")
async def health():
    """Detailed health check with service status."""
    status: dict = {"api": "ok"}

    try:
        from services.stock_data import get_stock_list  # noqa: PLC0415
        lst = get_stock_list()
        status["stock_data"] = f"ok ({len(lst)} symbols)"
    except Exception as exc:
        status["stock_data"] = f"error: {exc}"

    try:
        from services.stock_data import get_market_overview  # noqa: PLC0415
        get_market_overview()
        status["market_overview"] = "ok"
    except Exception as exc:
        status["market_overview"] = f"error: {exc}"

    all_ok = all(str(v).startswith("ok") for v in status.values())
    return {
        "healthy":  all_ok,
        "services": status,
    }


# ---------------------------------------------------------------------------
# Dev entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn  # noqa: PLC0415
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
