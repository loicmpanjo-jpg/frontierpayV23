# Africa Frontier Markets — Production Ready

## Architecture
- **EasyMarkets**: Trading platform with copy trading, social signals, wallet
- **FrontierPay**: Cross-border payments via Kora, Fincra, Flutterwave, Stripe
- **Revenue Engine**: 35% Ads / 50% Creator / 15% Platform split

## Quick Start
```bash
# 1. Configure
cp .env.example .env
# Edit: SECRET_KEY (>=48 chars), DB_PASSWORD, PSP API keys (LIVE)

# 2. Staging (Docker Compose)
docker-compose -f infra/docker-compose.prod.yml up -d

# 3. Verify
curl http://localhost:8000/health
curl http://localhost:8000/ready

# 4. Tests
pytest tests/ -v
```

## Production (Kubernetes)
```bash
kubectl apply -f infra/k8s/namespace.yml
kubectl apply -f infra/k8s/configmap.yml
# Edit infra/k8s/secrets.yml with real secrets
kubectl apply -f infra/k8s/secrets.yml
kubectl apply -f infra/k8s/postgres-deployment.yml
kubectl apply -f infra/k8s/redis-deployment.yml
kubectl apply -f infra/k8s/api-gateway-deployment.yml
kubectl apply -f infra/k8s/ingress.yml
kubectl apply -f infra/k8s/hpa.yml
```

## V45 Corrections Applied
1. ZoneInfo + weekend closed (market_registry.py)
2. SHA256 stable lock ID (payment_service.py)
3. SUPPORTED_CURRENCIES + amount>0 (wallet_service.py)
4. SelfFollowError + allocation>0 (copy_trading_service.py)
5. timedelta imported (platform_service.py)
6. TransactionType enum (main.py)
7. FX_TO_USD centralized (dashboard_service.py)
