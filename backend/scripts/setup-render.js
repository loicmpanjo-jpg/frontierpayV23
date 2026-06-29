const https = require('https');

const RENDER_API_KEY = process.env.RENDER_API_KEY;
const OWNER_ID = process.env.RENDER_OWNER_ID;

if (!RENDER_API_KEY || !OWNER_ID) {
  console.error('❌ Variables manquantes. Définir :');
  console.error('   export RENDER_API_KEY="rk_..."');
  console.error('   export RENDER_OWNER_ID="usr_..."');
  process.exit(1);
}

function apiRequest(path, method = 'GET', data = null) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.render.com',
      path: `/v1${path}`,
      method,
      headers: {
        'Authorization': `Bearer ${RENDER_API_KEY}`,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    };

    if (data) {
      options.headers['Content-Length'] = Buffer.byteLength(data);
    }

    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try {
          const parsed = JSON.parse(body);
          if (res.statusCode >= 400) {
            reject(new Error(`HTTP ${res.statusCode}: ${JSON.stringify(parsed)}`));
          } else {
            resolve(parsed);
          }
        } catch {
          resolve(body);
        }
      });
    });

    req.on('error', reject);
    if (data) req.write(data);
    req.end();
  });
}

function wait(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function deploy() {
  console.log('🚀 Déploiement COSY V0 sur Render...\n');

  try {
    // 1. Créer PostgreSQL
    console.log('📦 Étape 1/4 : Création PostgreSQL...');
    const dbData = JSON.stringify({
      name: 'cosy-db-v0',
      ownerId: OWNER_ID,
      region: 'frankfurt',
      plan: 'starter',
      version: '15',
      databaseName: 'cosy_v0',
      user: 'cosy_admin'
    });

    const db = await apiRequest('/postgres', 'POST', dbData);
    console.log(`   ✅ DB créée: ${db.id || db.postgres?.id}`);
    const dbId = db.id || db.postgres?.id;

    // 2. Attendre que la DB soit disponible
    console.log('⏳ Étape 2/4 : Attente disponibilité DB (peut prendre 2-3 min)...');
    let dbReady = false;
    let attempts = 0;
    let dbDetails;

    while (!dbReady && attempts < 30) {
      await wait(10000); // 10 secondes
      attempts++;
      try {
        dbDetails = await apiRequest(`/postgres/${dbId}`);
        if (dbDetails.status === 'available' || dbDetails.postgres?.status === 'available') {
          dbReady = true;
          console.log(`   ✅ DB disponible après ${attempts * 10}s`);
        } else {
          process.stdout.write('.');
        }
      } catch (e) {
        process.stdout.write('.');
      }
    }

    if (!dbReady) {
      console.error('\n❌ Timeout : La DB n'est pas devenue disponible');
      process.exit(1);
    }

    const dbUrl = dbDetails.connectionInfo?.internalConnectionString || 
                  dbDetails.postgres?.connectionInfo?.internalConnectionString;
    console.log(`   📡 URL interne DB : ${dbUrl?.substring(0, 50)}...`);

    // 3. Créer Web Service
    console.log('\n🌐 Étape 3/4 : Création Web Service...');

    // Lire les clés JWT
    const fs = require('fs');
    let privateKey, publicKey;
    try {
      privateKey = fs.readFileSync('./keys/jwt-private.pem', 'utf8');
      publicKey = fs.readFileSync('./keys/jwt-public.pem', 'utf8');
    } catch (e) {
      console.error('❌ Clés JWT non trouvées. Exécuter d'abord : ./scripts/generate-keys.sh');
      process.exit(1);
    }

    const serviceData = JSON.stringify({
      name: 'cosy-api',
      ownerId: OWNER_ID,
      region: 'frankfurt',
      type: 'web_service',
      runtime: 'node',
      plan: 'starter',
      buildCommand: 'npm install',
      startCommand: 'node server.js',
      envVars: [
        { key: 'NODE_ENV', value: 'production' },
        { key: 'DATABASE_URL', value: dbUrl },
        { key: 'JWT_PRIVATE_KEY', value: privateKey },
        { key: 'JWT_PUBLIC_KEY', value: publicKey },
        { key: 'JWT_EXPIRES_IN', value: '3600' },
        { key: 'REFRESH_TOKEN_EXPIRES_IN', value: '604800' },
        { key: 'OTP_EXPIRES_IN', value: '300' },
        { key: 'CORS_ORIGIN', value: '*' },
        { key: 'RATE_LIMIT_MAX', value: '100' }
      ]
    });

    const service = await apiRequest('/services', 'POST', serviceData);
    console.log(`   ✅ Service créé: ${service.id || service.service?.id}`);
    const serviceId = service.id || service.service?.id;

    // 4. Déployer le code (créer un deploy)
    console.log('\n📤 Étape 4/4 : Déploiement du code...');

    // Note : Render auto-deploy depuis Git. Pour l'instant, on affiche les infos.
    console.log('\n📋 RÉCAPITULATIF DU DÉPLOIEMENT');
    console.log('═══════════════════════════════════════');
    console.log(`🗄️  Database ID : ${dbId}`);
    console.log(`🌐 Service ID   : ${serviceId}`);
    console.log(`🔗 URL API      : https://cosy-api.onrender.com (après config)`);
    console.log('═══════════════════════════════════════\n');

    console.log('⚠️  IMPORTANT : Le code doit être pushé sur GitHub pour le déploiement auto.');
    console.log('   Étapes manuelles restantes :');
    console.log('   1. Créer un repo GitHub');
    console.log('   2. Push ce code : git init && git add . && git commit -m "init" && git push');
    console.log('   3. Connecter le repo dans Render Dashboard');
    console.log('   4. Render déploiera automatiquement\n');

    console.log('🎉 Configuration Render terminée!');

  } catch (err) {
    console.error('\n❌ Erreur:', err.message);
    process.exit(1);
  }
}

deploy();
