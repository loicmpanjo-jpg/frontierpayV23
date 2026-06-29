"""Génère les clés API pour Kaybic"""
import secrets
import sys


def generate_kaybic_credentials():
    api_key = f"kp_live_kaybic_{secrets.token_urlsafe(24)}"
    webhook_secret = f"whsec_{secrets.token_hex(32)}"

    print("=" * 60)
    print("KAYBIC/EASYTRANSFERT — CREDENTIALS DE PRODUCTION")
    print("=" * 60)
    print()
    print(f"API Key:        {api_key}")
    print(f"Webhook Secret: {webhook_secret}")
    print()
    print("Headers requis:")
    print(f'  Authorization: Bearer {api_key}')
    print(f'  X-Timestamp:   <unix_timestamp>')
    print(f'  X-Signature:   <hmac_sha256>')
    print()
    print("Base URL:")
    print("  https://api.frontierpay.com/v1/merchants/kaybic")
    print()
    print("Endpoints:")
    print("  POST /payments          → Créer paiement")
    print("  GET  /payments/{id}     → Statut")
    print("  GET  /quote             → Devis")
    print("  GET  /balance           → Solde")
    print("  POST /webhooks          → Config webhook")
    print()
    print("⚠️  CONSERVER CES CLÉS DANS UN VAULT SÉCURISÉ")
    print("=" * 60)


if __name__ == "__main__":
    generate_kaybic_credentials()
