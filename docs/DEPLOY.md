# COSY V0 — Guide de Déploiement Détaillé

## Option 1 : Render (Recommandé — Gratuit)

### Prérequis
- Compte Render.com (Sign up with Google)
- API Key Render (Account Settings → API Keys)
- Owner ID Render (Account Settings)

### Étapes
1. Générer les clés JWT:
   ```bash
   cd backend
   ./scripts/generate-keys.sh
   ```

2. Installer les dépendances:
   ```bash
   cd backend
   npm install
   ```

3. Déployer via le script:
   ```bash
   export RENDER_API_KEY="rk_..."
   export RENDER_OWNER_ID="usr_..."
   node scripts/setup-render.js
   ```

4. Migrer la base:
   ```bash
   npm run migrate
   npm run seed
   ```

### Limitations Free Tier
- Sleep après 15 min d'inactivité (cold start 30-50s)
- PostgreSQL gratuit expire en 90 jours
- Solution: Upgrader à $7/mois pour always-on

## Option 2 : Railway ($5/mois)

```bash
npm install -g @railway/cli
railway login
railway init
railway add postgres
railway add redis
railway up
```

## Option 3 : Docker Local (Développement)

```bash
# Démarrer l'infrastructure
docker-compose -f deploy/docker-compose.dev.yml up -d

# Installer les dépendances
cd backend && npm install

# Générer les clés
./scripts/generate-keys.sh

# Migrer et seeder
npm run migrate
npm run seed

# Démarrer le serveur
npm run dev
```

## Option 4 : VPS + Coolify (Production)

```bash
# Hetzner CX22 (€4.59/mois)
# Installer Coolify
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
# Déployer via l'interface web
```
