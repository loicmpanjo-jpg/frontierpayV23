# COSY V0 — API Documentation

## Base URL
- Local: `http://localhost:3000`
- Render: `https://cosy-api-xxx.onrender.com`

## Authentication
Tous les endpoints protégés nécessitent un header:
```
Authorization: Bearer <access_token>
```

## Endpoints

### Health
```
GET /health
→ { status: "ok", version: "0.1.0", services: {...} }
```

### Auth
```
POST /api/v0/auth/otp/request
  Body: { phone: "+237612345678" }
  → { message: "OTP envoyé", expires_in: 300 }

POST /api/v0/auth/otp/verify
  Body: { phone: "+237612345678", code: "123456", device_id: "abc" }
  → { access_token, refresh_token, expires_in, user }

POST /api/v0/auth/refresh
  Body: { refresh_token: "..." }
  → { access_token, expires_in }

GET /api/v0/auth/me
  Headers: Authorization: Bearer <token>
  → { id, phone, name, role, city, ... }

POST /api/v0/auth/logout
  Headers: Authorization: Bearer <token>
  → { message: "Déconnecté" }
```

### Users
```
GET /api/v0/users/me
PUT /api/v0/users/me
  Body: { name, username, city, genres, bio, avatar_url }

GET /api/v0/users/me/playlists
POST /api/v0/users/me/playlists
  Body: { name, description, track_ids, cover_url }

GET /api/v0/users/me/favorites
POST /api/v0/users/me/favorites
  Body: { track_id }

GET /api/v0/users/me/history
  Query: ?limit=50&offset=0
```

### Creators
```
POST /api/v0/creators
  Body: { stage_name, bio, city, country, genres, social_links, bank_info, mobile_money_number }

GET /api/v0/creators/:id
GET /api/v0/creators/:id/stats
  Query: ?period=7d|30d|90d|all
GET /api/v0/creators/:id/tracks
GET /api/v0/creators
  Query: ?city=Douala&status=active&verified=true&limit=20&offset=0
```

### Tracks
```
GET /api/v0/tracks
  Query: ?page=1&limit=20&city=Douala&genre=afropop&status=published

GET /api/v0/tracks/:id
GET /api/v0/tracks/search?q=...
```

### Streaming
```
POST /api/v0/streams
  Body: { track_id, session_id, duration, completed, context, device, quality, city }

GET /api/v0/streams/now-playing
  Query: ?city=Douala&limit=10

GET /api/v0/streams/trending
  Query: ?city=Douala&period=24h&genre=afropop&limit=50

GET /api/v0/streams/stats
  Query: ?track_id=xxx&period=7d
```

### Pulse
```
GET /api/v0/pulse/cities
GET /api/v0/pulse/:city
GET /api/v0/pulse/:city/tracks
  Query: ?period=24h&genre=afropop&limit=50
```

### Wallet
```
GET /api/v0/wallets/me
GET /api/v0/wallets/me/transactions
  Query: ?limit=50&offset=0&type=stream|ad|withdrawal|bonus

POST /api/v0/wallets/me/withdrawals
  Body: { amount, method: "mtn_momo|orange_money", phone_number, account_name }

GET /api/v0/wallets/me/withdrawals

GET /api/v0/wallets/withdrawals/pending
  Headers: X-Role: finance|admin (RBAC)

POST /api/v0/wallets/withdrawals/:id/approve
  Body: { transaction_reference }

POST /api/v0/wallets/withdrawals/:id/reject
  Body: { reason }
```

### Ads
```
POST /api/v0/campaigns
  Body: { name, budget_total, budget_daily, start_date, end_date, target, spot, format }

GET /api/v0/campaigns
GET /api/v0/campaigns/:id
GET /api/v0/ads/deliver
  Query: ?user_id=xxx&city=Douala&genre=afropop&hour=20
```

### AI
```
GET /api/v0/ai/score/:track_id
GET /api/v0/ai/moderation-queue
  Headers: X-Role: cco|admin

POST /api/v0/ai/moderation/:track_id/approve
  Body: { placement, notes }

POST /api/v0/ai/moderation/:track_id/reject
  Body: { reason, notes }
```

### Notifications
```
GET /api/v0/notifications/me
  Query: ?limit=50&unread_only=true

PUT /api/v0/notifications/:id/read
PUT /api/v0/notifications/read-all
```

### Radios
```
GET /api/v0/radios
  Query: ?city=Douala&status=active
GET /api/v0/radios/:id
```

## WebSocket
```
WS /ws/streams
  → { subscribe: "trending", city: "Douala" }
  ← { type: "trending_update", data: [...] }
```
