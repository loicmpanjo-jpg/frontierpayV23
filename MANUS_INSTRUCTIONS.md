# 🎵 COSY V0 — Instructions de Déploiement pour Manus AI

## 🎯 Objectif
Déployer automatiquement COSY V0 (API Node.js + PostgreSQL + Frontend SPA) sur Render.com

## 📦 Contenu du Pack

```
cosy-v0-manus-deploy/
├── MANUS_INSTRUCTIONS.md          ← Ce fichier
├── backend/
│   ├── server.js                  ← API Fastify complète (10 services)
│   ├── package.json               ← Dépendances Node.js
│   ├── .env.render                ← Config pré-remplie pour Render
│   ├── Dockerfile                 ← Conteneurisation optionnelle
│   ├── migrations/
│   │   └── 001_init_schema.sql    ← 20 tables PostgreSQL
│   ├── scripts/
│   │   ├── generate-keys.sh       ← Génération JWT RS256
│   │   ├── setup-render.js        ← API Render (création auto services)
│   │   ├── deploy-master.js       ← Script maître tout-en-un
│   │   ├── migrate.js             ← Exécution migrations
│   │   ├── seed.js                ← Données de test
│   │   └── test-api.js            ← Tests endpoints
│   └── keys/                      ← Clés JWT (générées à l'étape 2)
├── frontend/
│   └── cosy-app.html              ← SPA 17 écrans
├── deploy/
│   ├── render.yaml                ← Blueprint Render
│   ├── docker-compose.yml         ← Docker local/cloud
│   └── docker-compose.dev.yml     ← Dev local
└── docs/
    ├── API.md                     ← Documentation endpoints
    ├── PRD.md                     ← Product Requirements Document
    └── DEPLOY.md                  ← Guide déploiement détaillé
```

---

## 🚀 PROCÉDURE DE DÉPLOIEMENT — 7 ÉTAPES

### ÉTAPE 0 : Prérequis Utilisateur (TOI)

**Manus ne peut PAS faire ça à ta place :**
- [ ] Créer un compte Render.com (Sign up with Google)
- [ ] Générer une API Key Render (Account Settings → API Keys)
- [ ] Noter l'Owner ID (Account Settings)

**Résultat attendu :**
```
RENDER_API_KEY=rk_xxxxxxxxxxxxxxxx
RENDER_OWNER_ID=usr-xxxxxxxxxxxxxx
```

**Ensuite, donne ces 2 valeurs à Manus.**

---

### ÉTAPE 1 : Générer les clés JWT (Manus exécute)

```bash
cd backend
chmod +x scripts/generate-keys.sh
./scripts/generate-keys.sh
```

**Vérification :**
```bash
ls keys/
# Doit afficher : jwt-private.pem  jwt-public.pem
```

---

### ÉTAPE 2 : Installer les dépendances (Manus exécute)

```bash
cd backend
npm install
```

**Vérification :**
```bash
ls node_modules/ | head -5
# Doit afficher des dossiers comme @fastify, fastify, pg, etc.
```

---

### ÉTAPE 3 : Créer les services sur Render (Manus exécute)

```bash
cd backend
export RENDER_API_KEY="rk_xxxxxxxxxxxxxxxx"
export RENDER_OWNER_ID="usr-xxxxxxxxxxxxxx"
node scripts/setup-render.js
```

**Ce que fait le script :**
1. Crée PostgreSQL `cosy-db-v0` (plan gratuit)
2. Attend que la DB soit "available"
3. Récupère l'URL de connexion interne
4. Crée Web Service `cosy-api` (Node.js)
5. Configure les variables d'environnement
6. Déploie le code

**Sortie attendue :**
```
🚀 Déploiement COSY sur Render...
✅ DB créée: dpg-xxxxxxxx
⏳ Attente disponibilité DB...
✅ DB disponible
✅ Service créé: srv-xxxxxxxx
🎉 COSY déployé!
URL API: https://cosy-api-xxx.onrender.com
```

---

### ÉTAPE 4 : Migrer la base de données (Manus exécute)

**Attendre 2-3 minutes que le service soit déployé, puis :**

```bash
# Se connecter au shell Render du web service
# OU exécuter localement avec DATABASE_URL distant

# Option A : Via Render Dashboard → Shell
npm run migrate

# Option B : Local avec DB distante
export DATABASE_URL="postgres://..."  # URL interne Render
cd backend && npm run migrate
```

**Vérification :**
```bash
# Connexion à la DB distante
psql $DATABASE_URL -c "\dt"
# Doit afficher 20 tables
```

---

### ÉTAPE 5 : Seeder la base de données (Manus exécute)

```bash
cd backend
npm run seed
```

**Sortie attendue :**
```
🌱 Seeding COSY V0 database...
✅ Database seeded successfully!
   • 5 users (admin, cco, finance, artist, listener)
   • 1 creator (Salatiel)
   • 6 tracks
   • 3 radios
   • 1 campaign
   • AI scores + moderation queue
```

---

### ÉTAPE 6 : Tester l'API (Manus exécute)

```bash
cd backend
export API_URL="https://cosy-api-xxx.onrender.com"  # URL du service
node scripts/test-api.js
```

**Sortie attendue :**
```
🧪 Testing COSY API...
✅ Health: OK (200)
✅ Cities: OK (200) — Found 3 cities
✅ Trending: OK (200)
✅ OTP Request: OK (200)
🎉 API tests completed!
```

---

### ÉTAPE 7 : Déployer le frontend (Manus exécute)

**Option A — Render Static Site (Recommandé)**
```bash
# Dans Render Dashboard
# 1. "New Static Site"
# 2. Connecter le même repo
# 3. Publish directory: frontend
# 4. Build command: (vide)
```

**Option B — Netlify Drop (Plus rapide)**
```bash
# Aller sur https://app.netlify.com/drop
# Glisser-déposer le dossier frontend/
# URL générée instantanément
```

**Option C — GitHub Pages**
```bash
# Pusher frontend/cosy-app.html sur GitHub
# Activer GitHub Pages sur la branche
```

---

## 🔧 Configuration Post-Déploiement

### Variables d'environnement Render (vérifier)

Dans Render Dashboard → cosy-api → Environment :

```
NODE_ENV=production
DATABASE_URL=[auto-générée par Render]
JWT_PRIVATE_KEY_PATH=./keys/jwt-private.pem
JWT_PUBLIC_KEY_PATH=./keys/jwt-public.pem
JWT_EXPIRES_IN=3600
REFRESH_TOKEN_EXPIRES_IN=604800
OTP_EXPIRES_IN=300
CORS_ORIGIN=*
RATE_LIMIT_MAX=100
```

### URLs après déploiement

| Service | URL |
|---------|-----|
| API | `https://cosy-api-xxx.onrender.com` |
| Health | `https://cosy-api-xxx.onrender.com/health` |
| Swagger | `https://cosy-api-xxx.onrender.com/documentation` |
| Frontend | `https://cosy-frontend-xxx.onrender.com` |

---

## 🆘 Troubleshooting

| Problème | Cause | Solution |
|----------|-------|----------|
| `JWT keys not found` | Clés non générées | `./scripts/generate-keys.sh` |
| `ECONNREFUSED` | DB pas encore prête | Attendre 2-3 min, réessayer |
| `Build failed` | Dépendances manquantes | `npm install` local puis re-push |
| `Application Error` | Variables env manquantes | Vérifier toutes les env vars |
| Cold start (30s) | Render gratuit | Normal. Ping régulier ou upgrader |
| DB expire en 90j | Limitation Render Free | Exporter avant, réimporter |

---

## 📊 Coûts

| Phase | Plateforme | Coût | Durée |
|-------|-----------|------|-------|
| Test / Beta | Render Free | $0 | 90 jours DB |
| Production légère | Render Starter | $7/mois | Illimité |
| Production | Render Standard | $25/mois | Illimité |
| Alternative | Railway | $5/mois | Illimité |
| Alternative | Hetzner VPS | €4.59/mois | Illimité |

---

## 📞 Support

- **API Docs** : `docs/API.md`
- **PRD Complet** : `docs/PRD.md`
- **Guide Déploiement** : `docs/DEPLOY.md`

---

**COSY V0 — Douala Launch · Juillet 2026**
**Built for African creators. Powered by community.**
