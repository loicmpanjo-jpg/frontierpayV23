"""Production API Gateway. V45 Correction: TransactionType enum."""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from config.config import get_settings
from config.database import init_db, engine
from config.exceptions import AFMException
from config.logging_config import configure_logging
from config.rate_limit import rate_limiter
from config.security import decode_token
from config.telemetry import app_info, http_requests_total, http_request_duration, get_metrics_response, CONTENT_TYPE_LATEST
from event_bus.redis_producer import event_producer

logger = configure_logging()


class TransactionType(str, Enum):
    """V45 Correction: Enum for transaction types."""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    PAYMENT = "payment"
    TRADE = "trade"
    COPY_TRADE = "copy_trade"
    FEE = "fee"
    REVENUE_SPLIT = "revenue_split"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    settings = get_settings()
    app_info.info({
        "version": "prod-1.0.0",
        "environment": settings.environment,
    })
    logger.info("Starting Africa Frontier Markets API", environment=settings.environment)
    await init_db()
    yield
    logger.info("Shutting down gracefully...")
    await event_producer.close()
    await rate_limiter.close()
    await engine.dispose()
    logger.info("Shutdown complete")


app = FastAPI(
    title="Africa Frontier Markets API",
    description="Unified API for EasyMarkets trading and FrontierPay payments",
    version="prod-1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if get_settings().is_development else None,
    redoc_url="/redoc" if get_settings().is_development else None,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Idempotency-Key"],
    max_age=600,
)


@app.exception_handler(AFMException)
async def afm_exception_handler(request: Request, exc: AFMException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "detail": exc.detail},
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = datetime.now(timezone.utc)
    request_id = request.headers.get("X-Request-ID", "unknown")

    import structlog
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id, path=request.url.path)

    response = await call_next(request)

    duration = (datetime.now(timezone.utc) - start).total_seconds()
    http_request_duration.labels(
        method=request.method,
        endpoint=request.url.path,
    ).observe(duration)
    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code,
    ).inc()

    logger.info(
        "Request completed",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round(duration * 1000, 2),
    )

    return response


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/ready")
async def readiness_check():
    checks = {
        "database": await _check_database(),
        "redis": await _check_redis(),
    }
    all_ready = all(checks.values())

    if not all_ready:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "checks": checks},
        )

    return {"status": "ready", "checks": checks}


async def _check_database() -> bool:
    try:
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def _check_redis() -> bool:
    try:
        import redis.asyncio as redis
        client = redis.from_url(settings.redis_url, decode_responses=True)
        await client.ping()
        await client.close()
        return True
    except Exception:
        return False


@app.get("/metrics")
async def metrics():
    return PlainTextResponse(
        content=get_metrics_response(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/")
async def root():
    return {
        "name": "Africa Frontier Markets",
        "version": "prod-1.0.0",
        "status": "operational",
    }


async def get_current_user(request: Request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = auth[7:]
    try:
        payload = decode_token(token)
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


async def rate_limit(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    await rate_limiter.is_allowed(
        f"ip:{client_ip}",
        limit=100,
        window_seconds=60,
    )
    return True


@app.get("/api/v1/wallet/balance", dependencies=[Depends(rate_limit)])
async def get_wallet_balance(user=Depends(get_current_user)):
    return {"user_id": user.get("sub"), "balances": {}}


@app.post("/webhooks/kora")
async def kora_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get("X-Kora-Signature", "")

    from payment_hub.payment_service import payment_service
    if not await payment_service.verify_webhook("kora", payload, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    data = await request.json()
    logger.info("Kora webhook received", event=data.get("event"))
    return {"status": "received"}


@app.post("/webhooks/fincra")
async def fincra_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get("X-Fincra-Signature", "")

    from payment_hub.payment_service import payment_service
    if not await payment_service.verify_webhook("fincra", payload, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    data = await request.json()
    logger.info("Fincra webhook received", event=data.get("event"))
    return {"status": "received"}


@app.post("/platforms")
async def onboard_platform(request: Request):
    from platform_manager.platform_service import platform_service
    data = await request.json()
    result = await platform_service.onboard_platform(
        name=data["name"],
        contact_email=data["contact_email"],
        webhook_url=data.get("webhook_url"),
    )
    return result


@app.post("/platforms/{platform_id}/rotate-key")
async def rotate_api_key(platform_id: str, user=Depends(get_current_user)):
    from platform_manager.platform_service import platform_service
    result = await platform_service.rotate_key(platform_id)
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        access_log=False,
    )
