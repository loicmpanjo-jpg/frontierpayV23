"""FrontierPay V23 — Kaybic Integration + Dashboard + AI Support"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import init_db
from app.core.config import settings
from app.core.exceptions import FrontierPayException, frontierpay_exception_handler

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 Starting {settings.APP_NAME} V{settings.VERSION}")
    await init_db()
    print("✅ Database initialized")
    yield
    print("🛑 Shutting down FrontierPay V23")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="""
    FrontierPay V23 — Orchestrateur de paiements cross-border

    • Kaybic/EasyTransfert Integration (Merchant API)
    • KoraPay = PSP principal Afrique
    • Fincra = PSP Afrique + Amérique + Asie
    • Payoneer = Fallback global
    • Dashboard Admin temps réel
    • IA Support intégrée
    """,
    lifespan=lifespan
)

app.add_exception_handler(FrontierPayException, frontierpay_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
from app.api.routes import merchant_kaybic
from app.api.admin import dashboard
from app.api.support import ai_support

app.include_router(merchant_kaybic.router)
app.include_router(dashboard.router)
app.include_router(ai_support.router)

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": settings.VERSION,
        "features": [
            "kaybic_merchant_api",
            "kora_rail_africa",
            "fincra_rail_global",
            "intelligent_routing",
            "admin_dashboard",
            "ai_support",
            "circuit_breaker",
            "encryption_at_rest",
        ]
    }

@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
        "kaybic_api": "/v1/merchants/kaybic",
        "admin_dashboard": "/admin/v1/dashboard/summary",
        "ai_support": "/support/v1/chat",
    }
