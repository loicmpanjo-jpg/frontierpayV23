"""AI Support — Assistant intelligent pour merchants et ops"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from app.core.config import settings
from app.core.database import get_db
from app.models import SupportTicket

router = APIRouter(prefix="/support/v1", tags=["AI Support"])


class FrontierPayAI:
    """
    IA Support pour:
    - Répondre aux questions d'intégration Kaybic
    - Diagnostiquer les transactions
    - Suggérer des optimisations de routing
    - Générer des rapports
    """

    SYSTEM_PROMPT = """Tu es l'assistant IA de FrontierPay, spécialisé dans les paiements cross-border Africa.

    Contexte système:
    - FrontierPay est un orchestrateur de paiements (pas de conservation de fonds)
    - KoraPay = PSP principal Afrique (CM, NG, GH, KE, CI, EG, TZ)
    - Fincra = PSP secondaire (Afrique + Amérique + Asie)
    - Payoneer = fallback global
    - Kaybic/EasyTransfert = merchant premium partner

    Tu peux:
    1. Expliquer l'API Kaybic
    2. Diagnostiquer une transaction par son ID
    3. Expliquer les frais et le pricing
    4. Suggérer des optimisations de corridor
    5. Répondre aux questions KYC/compliance

    Ne révèle JAMAIS les détails internes PSP (clés API, fee structure exacte).
    """

    def __init__(self):
        self.model = settings.AI_MODEL

    async def chat(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Traite un message et retourne une réponse"""

        message_lower = message.lower()

        # Détection d'intention
        if "transaction" in message_lower and any(c.isdigit() for c in message):
            return await self._diagnose_transaction(message)

        if "frais" in message_lower or "fee" in message_lower or "pricing" in message_lower:
            return self._explain_pricing()

        if "api" in message_lower or "endpoint" in message_lower or "integration" in message_lower:
            return self._explain_api()

        if "kora" in message_lower or "fincra" in message_lower:
            return self._explain_psp_routing()

        if "corridor" in message_lower:
            return self._suggest_corridors()

        if "kyc" in message_lower or "compliance" in message_lower:
            return self._explain_compliance()

        # Réponse générique
        return {
            "response": "Je suis l'assistant IA FrontierPay. Je peux vous aider avec :\n"
                       "• L'intégration API Kaybic\n"
                       "• Le diagnostic de transactions\n"
                       "• L'explication des frais et pricing\n"
                       "• Les optimisations de corridor\n"
                       "• Le KYC et compliance\n\n"
                       "Posez-moi votre question !",
            "suggestions": [
                "Comment intégrer l'API ?",
                "Quels sont les frais pour CM→NG ?",
                "Transaction fp_abc123 en erreur",
                "Quels corridors sont disponibles ?",
            ],
            "confidence": 0.9,
        }

    async def _diagnose_transaction(self, message: str) -> Dict[str, Any]:
        """Extrait l'ID transaction et simule un diagnostic"""
        words = message.split()
        tx_id = None
        for w in words:
            if w.startswith("fp_") or len(w) == 12:
                tx_id = w
                break

        if not tx_id:
            return {
                "response": "Je n'ai pas trouvé d'ID transaction valide. Format attendu: fp_xxxxxxxxx",
                "confidence": 0.8,
            }

        return {
            "response": f"🔍 Diagnostic transaction **{tx_id}**\n\n"
                       f"**Statut:** processing → collected → payout_pending\n"
                       f"**Collection:** KoraPay (XAF) — ✅ Succès en 2min\n"
                       f"**Payout:** Fincra (NGN) — ⏳ En cours (est. 8min)\n"
                       f"**Progrès:** 75% — Payout initié, attente confirmation bénéficiaire\n\n"
                       f"**Actions suggérées:**\n"
                       f"• Attendre 10 minutes max\n"
                       f"• Si échec: fallback automatique vers KoraPay\n"
                       f"• Contacter support@frontierpay.com si >30min",
            "transaction_id": tx_id,
            "confidence": 0.92,
            "actions": [
                {"label": "Voir détails", "url": f"/admin/v1/transactions/{tx_id}"},
                {"label": "Forcer retry", "action": "retry_payout"},
            ],
        }

    def _explain_pricing(self) -> Dict[str, Any]:
        return {
            "response": "💰 **Structure tarifaire FrontierPay**\n\n"
                       "Notre pricing est transparent :\n\n"
                       "**Formule:**\n```\nTarif client = Coût PSP + Markup FrontierPay\n```\n\n"
                       "**Coût PSP (exemple CM→NG):**\n"
                       "• KoraPay collecte XAF: ~2.5%\n"
                       "• KoraPay payout NGN: ~1.5%\n"
                       "• **Total PSP: ~4.0%**\n\n"
                       "**Markup FrontierPay:**\n"
                       "• Base: 0.5%\n"
                       "• Volume >100M/mois: -0.2%\n"
                       "• High-risk: +0.3%\n"
                       "• Speed <1h: +0.2%\n"
                       "• Fallback Payoneer: +0.5%\n\n"
                       "**Exemple:** 50,000 XAF → NGN\n"
                       "• Frais PSP: 2,000 XAF (4%)\n"
                       "• Markup: 250 XAF (0.5%)\n"
                       "• **Total: 2,250 XAF (4.5%)**\n"
                       "• Net: 47,750 XAF",
            "confidence": 0.95,
        }

    def _explain_api(self) -> Dict[str, Any]:
        return {
            "response": "🔌 **Intégration API Kaybic — Quick Start**\n\n"
                       "**1. Authentification**\n```\nHeaders:\n  Authorization: Bearer kp_live_xxx\n  X-Timestamp: 1719412800\n  X-Signature: hmac_sha256(...)\n```\n\n"
                       "**2. Créer un paiement**\n```\nPOST /v1/merchants/kaybic/payments\n{\n  \"idempotency_key\": \"kaybic_txn_001\",\n  \"amount\": 50000,\n  \"currency\": \"XAF\",\n  \"source\": {\n    \"country\": \"CM\",\n    \"method\": \"mobile_money\",\n    \"phone\": \"+237699123456\"\n  },\n  \"destination\": {\n    \"country\": \"NG\",\n    \"method\": \"mobile_money\",\n    \"phone\": \"+2348012345678\"\n  }\n}\n```\n\n"
                       "**3. Devis avant paiement**\n```\nGET /v1/merchants/kaybic/quote?amount=50000&source_country=CM&destination_country=NG\n```\n\n"
                       "**4. Webhooks**\n"
                       "Configurez votre URL webhook pour recevoir les événements:\n"
                       "• payment.initiated\n"
                       "• payment.completed\n"
                       "• payment.failed\n\n"
                       "**Documentation complète:** /docs",
            "confidence": 0.93,
            "code_examples": [
                {"lang": "curl", "code": "curl -X POST https://api.frontierpay.com/v1/merchants/kaybic/payments ..."},
                {"lang": "python", "code": "import requests\nresponse = requests.post(...)"},
            ],
        }

    def _explain_psp_routing(self) -> Dict[str, Any]:
        return {
            "response": "🌍 **Routing PSP — Comment ça marche**\n\n"
                       "Vous ne voyez jamais Kora ou Fincra directement. FrontierPay choisit automatiquement.\n\n"
                       "**Logique de routing:**\n\n"
                       "| Corridor | Collecte | Payout | Pourquoi ? |\n"
                       "|----------|----------|--------|------------|\n"
                       "| CM → NG | KoraPay | KoraPay | Kora dominant les deux marchés |\n"
                       "| CM → GH | KoraPay | KoraPay | Kora présent GH |\n"
                       "| NG → KE | Fincra | Fincra | Fincra couvre NG+KE |\n"
                       "| NG → US | Fincra | Fincra | Fincra a le rail US |\n"
                       "| NG → IN | Fincra | Fincra | Fincra a le rail Inde |\n"
                       "| GH → NG | KoraPay | KoraPay | Kora dominant les deux |\n\n"
                       "**Priorités:**\n"
                       "1. Coût (défaut)\n"
                       "2. Vitesse (<1h)\n"
                       "3. Fiabilité (99%+)\n\n"
                       "**Fallback:** Si Kora indisponible → Fincra → Payoneer",
            "confidence": 0.94,
        }

    def _suggest_corridors(self) -> Dict[str, Any]:
        return {
            "response": "🛣️ **Corridors disponibles — Juin 2026**\n\n"
                       "**Afrique → Afrique (KoraPay principal):**\n"
                       "• CM ↔ NG (XAF↔NGN) — Mobile Money\n"
                       "• CM ↔ GH (XAF↔GHS) — Mobile Money\n"
                       "• NG ↔ GH (NGN↔GHS) — Mobile Money\n"
                       "• NG → KE (NGN→KES) — Fincra\n"
                       "• CI → NG (XOF→NGN) — Fincra\n\n"
                       "**Afrique → Global (Fincra principal):**\n"
                       "• NG → US (NGN→USD) — Bank Transfer\n"
                       "• NG → UK (NGN→GBP) — Bank Transfer\n"
                       "• NG → IN (NGN→INR) — Bank Transfer / Cash Pickup\n"
                       "• GH → US (GHS→USD) — Bank Transfer\n"
                       "• KE → UK (KES→GBP) — Bank Transfer\n\n"
                       "**Nouveaux corridors (beta):**\n"
                       "• CM → FR (XAF→EUR) — SEPA\n"
                       "• NG → CA (NGN→CAD) — Bank Transfer",
            "confidence": 0.91,
        }

    def _explain_compliance(self) -> Dict[str, Any]:
        return {
            "response": "🛡️ **Compliance & KYC**\n\n"
                       "**Pour Kaybic (déjà KYB):**\n"
                       "• Vos clients finaux: KYC light (nom, téléphone, ID)\n"
                       "• Transactions <500K: automatique\n"
                       "• Transactions >500K: revue manuelle possible\n\n"
                       "**AML checks:**\n"
                       "• Sanctions screening (OFAC, UN, EU)\n"
                       "• Velocity checks\n"
                       "• Pattern detection\n\n"
                       "**Documents requis selon corridor:**\n"
                       "• CM→NG: RI (Référence d'Identité) ou passeport\n"
                       "• NG→US: Preuve d'adresse + source de fonds\n"
                       "• >1M/mois: EDD (Enhanced Due Diligence)\n\n"
                       "**Délai KYC:** 2-5 minutes (automatique) / 24h (manuel)",
            "confidence": 0.88,
        }


ai = FrontierPayAI()


@router.post("/chat")
async def chat_support(
    message: str,
    merchant_code: Optional[str] = None,
    conversation_id: Optional[str] = None,
):
    """Chat avec l'IA Support"""
    response = await ai.chat(message)
    return {
        "conversation_id": conversation_id or f"conv_{datetime.utcnow().timestamp()}",
        "message": message,
        "response": response["response"],
        "confidence": response["confidence"],
        "suggestions": response.get("suggestions", []),
        "actions": response.get("actions", []),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/tickets")
async def create_ticket(
    subject: str,
    description: str,
    merchant_code: Optional[str] = None,
    priority: str = "medium",
    db=Depends(get_db)
):
    """Crée un ticket support avec suggestion IA"""
    ticket_number = f"FP-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    # IA analyse et suggère
    ai_analysis = await ai.chat(f"Ticket: {subject}. Description: {description}")

    ticket = SupportTicket(
        ticket_number=ticket_number,
        subject=subject,
        description=description,
        priority=priority,
        ai_suggestions=[ai_analysis["response"]],
        ai_confidence=ai_analysis["confidence"],
    )

    db.add(ticket)
    await db.commit()

    return {
        "ticket_number": ticket_number,
        "status": "open",
        "ai_suggestion": ai_analysis["response"],
        "estimated_resolution": "4 hours" if priority == "high" else "24 hours",
    }


@router.get("/tickets/{ticket_number}")
async def get_ticket(ticket_number: str, db=Depends(get_db)):
    """Récupère un ticket"""
    from sqlalchemy import select
    result = await db.execute(
        select(SupportTicket).where(SupportTicket.ticket_number == ticket_number)
    )
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return {
        "ticket_number": ticket.ticket_number,
        "subject": ticket.subject,
        "status": ticket.status,
        "priority": ticket.priority,
        "ai_suggestions": ticket.ai_suggestions,
        "resolution_notes": ticket.resolution_notes,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
    }
