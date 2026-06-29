"""Admin Dashboard API — Transactions globales, analytics, monitoring"""
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import func, select, and_, desc

from app.core.database import get_db
from app.core.security import verify_jwt_token
from app.models import Transaction, Merchant, PSPProvider, SettlementPosition

router = APIRouter(prefix="/admin/v1", tags=["Admin Dashboard"])

security = HTTPBearer(auto_error=False)


async def verify_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    payload = verify_jwt_token(credentials.credentials)
    if not payload or payload.get("role") not in ["admin", "superadmin", "operator"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return payload


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    admin: Dict = Depends(verify_admin),
    db=Depends(get_db)
):
    """Vue d'ensemble du dashboard"""
    # Stats transactions
    result = await db.execute(select(func.count(Transaction.id)).where(
        Transaction.created_at >= datetime.utcnow() - timedelta(days=1)
    ))
    transactions_24h = result.scalar()

    result = await db.execute(select(func.sum(Transaction.amount)).where(
        Transaction.status == "completed",
        Transaction.created_at >= datetime.utcnow() - timedelta(days=1)
    ))
    volume_24h = result.scalar() or 0

    result = await db.execute(select(func.sum(Transaction.net_margin)).where(
        Transaction.created_at >= datetime.utcnow() - timedelta(days=30)
    ))
    revenue_30d = result.scalar() or 0

    # PSP Health
    psps = await db.execute(select(PSPProvider))
    psp_health = []
    for psp in psps.scalars():
        psp_health.append({
            "name": psp.name,
            "code": psp.psp_code,
            "status": psp.status,
            "health_score": psp.health_score,
            "success_rate": psp.success_rate_7d,
            "current_exposure": psp.current_exposure,
            "exposure_limit": psp.exposure_limit,
            "circuit_state": psp.circuit_state,
        })

    # Settlement positions
    positions = await db.execute(select(SettlementPosition))
    settlement = []
    for pos in positions.scalars():
        settlement.append({
            "currency": pos.currency,
            "available": pos.available_balance,
            "pending_in": pos.pending_incoming,
            "pending_out": pos.pending_outgoing,
            "reserved": pos.reserved_for_settlement,
            "efficiency": pos.capital_efficiency,
        })

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "transactions": {
            "last_24h": transactions_24h,
            "volume_24h": round(volume_24h, 2),
            "success_rate": 0.97,
        },
        "revenue": {
            "last_30d": round(revenue_30d, 2),
            "avg_margin_pct": 0.65,
        },
        "psp_health": psp_health,
        "settlement_positions": settlement,
        "alerts": [
            {"level": "warning", "message": "Kora exposure at 78%"},
            {"level": "info", "message": "Fincra new corridor CI→US available"},
        ]
    }


@router.get("/transactions")
async def list_transactions(
    status: Optional[str] = None,
    merchant_code: Optional[str] = None,
    psp: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    page: int = 1, limit: int = 50,
    admin: Dict = Depends(verify_admin),
    db=Depends(get_db)
):
    """Liste toutes les transactions avec filtres"""
    query = select(Transaction).order_by(desc(Transaction.created_at))

    if status:
        query = query.where(Transaction.status == status)
    if from_date:
        query = query.where(Transaction.created_at >= from_date)
    if to_date:
        query = query.where(Transaction.created_at <= to_date)
    if psp:
        query = query.where(
            (Transaction.collection_psp == psp) | (Transaction.payout_psp == psp)
        )

    if merchant_code:
        merchant = await db.execute(
            select(Merchant).where(Merchant.merchant_code == merchant_code)
        )
        merchant = merchant.scalar_one_or_none()
        if merchant:
            query = query.where(Transaction.merchant_id == merchant.id)

    # Pagination
    total = await db.execute(select(func.count()).select_from(query.subquery()))
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    transactions = []
    for tx in result.scalars():
        transactions.append({
            "id": str(tx.id),
            "transaction_code": tx.transaction_code,
            "amount": tx.amount,
            "currency": tx.origin_currency,
            "status": tx.status,
            "collection_psp": tx.collection_psp,
            "payout_psp": tx.payout_psp,
            "net_margin": tx.net_margin,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
        })

    return {
        "total": total.scalar(),
        "page": page,
        "limit": limit,
        "transactions": transactions,
    }


@router.get("/transactions/{transaction_id}")
async def get_transaction_detail(
    transaction_id: str,
    admin: Dict = Depends(verify_admin),
    db=Depends(get_db)
):
    """Détail complet d'une transaction (interne)"""
    result = await db.execute(
        select(Transaction).where(Transaction.id == transaction_id)
    )
    tx = result.scalar_one_or_none()

    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return {
        "id": str(tx.id),
        "transaction_code": tx.transaction_code,
        "idempotency_key": tx.idempotency_key,
        "amount": tx.amount,
        "origin_currency": tx.origin_currency,
        "destination_currency": tx.destination_currency,
        "fx_rate": tx.fx_rate,
        "collection": {
            "psp": tx.collection_psp,
            "fee": tx.psp_fee,
        },
        "payout": {
            "psp": tx.payout_psp,
            "fee": tx.settlement_fee,
        },
        "frontierpay_markup": tx.frontierpay_markup,
        "total_cost": tx.total_cost,
        "net_margin": tx.net_margin,
        "net_margin_pct": tx.net_margin_pct,
        "status": tx.status,
        "status_history": tx.status_history,
        "source_data": tx.source_data,
        "destination_data": tx.destination_data,
        "metadata": tx.metadata,
        "created_at": tx.created_at.isoformat() if tx.created_at else None,
        "updated_at": tx.updated_at.isoformat() if tx.updated_at else None,
    }


@router.get("/merchants")
async def list_merchants(
    status: Optional[str] = None,
    admin: Dict = Depends(verify_admin),
    db=Depends(get_db)
):
    """Liste des merchants"""
    query = select(Merchant)
    if status:
        query = query.where(Merchant.is_active == (status == "active"))

    result = await db.execute(query)
    merchants = []
    for m in result.scalars():
        merchants.append({
            "id": str(m.id),
            "code": m.merchant_code,
            "name": m.name,
            "email": m.email,
            "country": m.country,
            "risk_score": m.risk_score,
            "risk_tier": m.risk_tier,
            "daily_volume": m.daily_volume,
            "monthly_volume": m.monthly_volume,
            "kyc_status": m.kyc_status,
            "is_active": m.is_active,
        })
    return {"merchants": merchants}


@router.get("/analytics/corridors")
async def corridor_analytics(
    days: int = 30,
    admin: Dict = Depends(verify_admin),
    db=Depends(get_db)
):
    """Analytics par corridor"""
    from_date = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(
            Transaction.corridor_id,
            func.count(Transaction.id).label("count"),
            func.sum(Transaction.amount).label("volume"),
            func.sum(Transaction.net_margin).label("revenue"),
        )
        .where(Transaction.created_at >= from_date)
        .group_by(Transaction.corridor_id)
    )

    corridors = []
    for row in result.all():
        corridors.append({
            "corridor_id": str(row.corridor_id),
            "transaction_count": row.count,
            "volume": round(row.volume or 0, 2),
            "revenue": round(row.revenue or 0, 2),
        })

    return {"period_days": days, "corridors": corridors}


@router.get("/analytics/psp-performance")
async def psp_performance(
    days: int = 7,
    admin: Dict = Depends(verify_admin),
    db=Depends(get_db)
):
    """Performance par PSP"""
    from_date = datetime.utcnow() - timedelta(days=days)

    # Kora stats
    kora_result = await db.execute(
        select(
            func.count(Transaction.id),
            func.sum(Transaction.amount),
            func.avg(Transaction.psp_fee),
        )
        .where(
            Transaction.created_at >= from_date,
            (Transaction.collection_psp == "kora") | (Transaction.payout_psp == "kora")
        )
    )
    kora_count, kora_volume, kora_avg_fee = kora_result.first()

    # Fincra stats
    fincra_result = await db.execute(
        select(
            func.count(Transaction.id),
            func.sum(Transaction.amount),
            func.avg(Transaction.psp_fee),
        )
        .where(
            Transaction.created_at >= from_date,
            (Transaction.collection_psp == "fincra") | (Transaction.payout_psp == "fincra")
        )
    )
    fincra_count, fincra_volume, fincra_avg_fee = fincra_result.first()

    return {
        "period_days": days,
        "psps": [
            {
                "name": "KoraPay",
                "transactions": kora_count or 0,
                "volume": round(kora_volume or 0, 2),
                "avg_fee": round(kora_avg_fee or 0, 4),
                "market_share": round((kora_count or 0) / ((kora_count or 0) + (fincra_count or 0)) * 100, 1) if (kora_count or fincra_count) else 0,
            },
            {
                "name": "Fincra",
                "transactions": fincra_count or 0,
                "volume": round(fincra_volume or 0, 2),
                "avg_fee": round(fincra_avg_fee or 0, 4),
                "market_share": round((fincra_count or 0) / ((kora_count or 0) + (fincra_count or 0)) * 100, 1) if (kora_count or fincra_count) else 0,
            },
        ]
    }


# WebSocket pour temps réel
@router.websocket("/ws/live")
async def websocket_dashboard(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            import asyncio
            # Envoyer stats toutes les 5 secondes
            data = {
                "timestamp": datetime.utcnow().isoformat(),
                "active_transactions": 12,
                "tps": 3.5,
            }
            await websocket.send_json(data)
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass
