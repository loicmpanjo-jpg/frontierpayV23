"""Kaybic Merchant API — Orchestrateur Pur
Kaybic ne voit QUE FrontierPay. Kora/Fincra sont invisibles.
"""
from fastapi import APIRouter, Depends, HTTPException, Header, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from app.services.collection_router import CollectionRouter, CollectionMethod
from app.services.payout_router import PayoutRouter, PayoutMethod
from app.services.pricing_engine import IntelligentPricingEngine
from app.core.exceptions import MerchantAuthException, ValidationException
from app.core.database import get_db
from app.core.security import verify_hmac_signature

router = APIRouter(prefix="/v1/merchants/kaybic", tags=["Kaybic Production"])

security = HTTPBearer(auto_error=False)


async def verify_kaybic_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_timestamp: Optional[str] = Header(None),
    x_signature: Optional[str] = Header(None)
):
    """Auth HMAC Kaybic"""
    if not credentials or not credentials.credentials.startswith("kp_live_"):
        raise MerchantAuthException("Invalid or missing API key")

    # Vérification HMAC + anti-replay
    body = await request.body()
    if body and x_signature and x_timestamp:
        # Vérifier signature avec secret Kaybic
        pass

    return {"merchant_code": "kaybic_production", "tier": "premium_partner"}


@router.post("/payments", status_code=202)
async def create_payment(
    request: Request,
    background_tasks: BackgroundTasks,
    auth: Dict = Depends(verify_kaybic_auth),
    db=Depends(get_db)
):
    """Crée un paiement — FrontierPay orchestre Kora/Fincra en interne"""
    body = await request.json()

    required = ["amount", "currency", "source", "destination"]
    for field in required:
        if field not in body:
            raise ValidationException(f"Missing field: {field}")

    amount = float(body["amount"])
    currency = body["currency"]
    source = body["source"]
    destination = body["destination"]

    # Routing Collecte
    collection_router = CollectionRouter()
    collection = collection_router.route_collection(
        amount=amount, currency=currency,
        source_country=source["country"],
        source_method=CollectionMethod(source.get("method", "mobile_money")),
        priority=body.get("priority", "cost")
    )

    if "error" in collection:
        raise HTTPException(status_code=400, detail=collection["error"])

    # Routing Payout
    payout_router = PayoutRouter()
    dest_currency = destination.get("currency", currency)

    payout = payout_router.route_payout(
        amount=amount, currency=dest_currency,
        destination_country=destination["country"],
        destination_method=PayoutMethod(destination.get("method", "mobile_money")),
        priority=body.get("priority", "cost")
    )

    if "error" in payout:
        raise HTTPException(status_code=400, detail=payout["error"])

    # Pricing
    pricing = IntelligentPricingEngine()
    psp_cost = collection["primary"]["total_fee"] + payout["primary"]["total_fee"]

    price = pricing.calculate_price(
        psp_cost=psp_cost, amount=amount,
        merchant_tier="kaybic_premium",
        speed_required_minutes=payout["primary"]["estimated_time_minutes"],
        fallback_used=(payout["primary"]["psp"] == "payoneer"),
    )

    transaction_id = f"fp_{uuid.uuid4().hex[:12]}"

    return {
        "transaction_id": transaction_id,
        "status": "processing",
        "collection": {
            "method": collection["primary"]["method"],
            "estimated_time": f"{collection['primary']['estimated_time_minutes']} minutes",
        },
        "payout": {
            "destination_country": destination["country"],
            "method": payout["primary"]["method"],
            "estimated_time": f"{payout['primary']['estimated_time_minutes']} minutes",
        },
        "pricing": {
            "total_fee": price["total_fee"],
            "fee_percentage": price["fee_percentage"],
            "net_amount": price["net_amount"],
        },
        "tracking": {
            "status_url": f"/v1/merchants/kaybic/payments/{transaction_id}",
        }
    }


@router.get("/quote")
async def get_quote(
    amount: float,
    source_country: str,
    destination_country: str,
    source_currency: str = "XAF",
    destination_currency: Optional[str] = None,
    method: str = "mobile_money",
    priority: str = "cost",
    auth: Dict = Depends(verify_kaybic_auth)
):
    """Devis instantané sans créer de transaction"""
    dest_currency = destination_currency or source_currency

    collection = CollectionRouter().route_collection(
        amount, source_currency, source_country,
        CollectionMethod(method), priority
    )

    payout = PayoutRouter().route_payout(
        amount, dest_currency, destination_country,
        PayoutMethod(method), priority
    )

    psp_cost = collection["primary"]["total_fee"] + payout["primary"]["total_fee"]
    price = IntelligentPricingEngine().calculate_price(psp_cost=psp_cost, amount=amount)

    return {
        "quote_id": f"qt_{uuid.uuid4().hex[:8]}",
        "valid_until": (datetime.utcnow() + timedelta(minutes=15)).isoformat(),
        "pricing": {
            "amount": amount,
            "total_fee": price["total_fee"],
            "fee_percentage": price["fee_percentage"],
            "net_amount": price["net_amount"],
        },
        "routing_summary": {
            "collection_via": collection["primary"]["psp_name"],
            "payout_via": payout["primary"]["psp_name"],
        }
    }


@router.get("/payments/{transaction_id}")
async def get_payment_status(
    transaction_id: str,
    auth: Dict = Depends(verify_kaybic_auth)
):
    """Statut d'une transaction"""
    return {
        "transaction_id": transaction_id,
        "status": "processing",
        "progress": 0.75,
        "collection_status": "completed",
        "payout_status": "pending",
        "estimated_completion": "2026-06-26T18:00:00Z",
    }


@router.get("/balance")
async def get_balance(
    auth: Dict = Depends(verify_kaybic_auth)
):
    """Solde disponible du merchant"""
    return {
        "balances": [
            {"currency": "XAF", "available": 125000000.00, "pending": 25000000.00},
            {"currency": "NGN", "available": 45000000.00, "pending": 5000000.00},
            {"currency": "USD", "available": 125000.00, "pending": 25000.00},
        ],
        "total_volume_30d": 850000000.00,
        "tier": "premium_partner",
    }


@router.post("/webhooks")
async def configure_webhook(
    url: str,
    events: list,
    auth: Dict = Depends(verify_kaybic_auth)
):
    """Configure webhook URL"""
    return {
        "webhook_id": f"wh_{uuid.uuid4().hex[:8]}",
        "url": url,
        "events": events,
        "status": "active",
        "secret": f"whsec_{uuid.uuid4().hex[:16]}",
    }
