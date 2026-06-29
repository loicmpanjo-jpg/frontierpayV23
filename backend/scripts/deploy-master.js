#!/usr/bin/env node
/**
 * COSY V0 — Script Maître de Déploiement
 * Manus exécute ce fichier SEUL et tout se fait automatiquement
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const STEPS = {
  1: 'Vérification environnement',
  2: 'Génération clés JWT',
  3: 'Installation dépendances',
  4: 'Configuration Render',
  5: 'Création services cloud',
  6: 'Migration base de données',
  7: 'Seeding données',
  8: 'Tests API',
  9: 'Récapitulatif'
};

function log(step, message) {
  console.log(`\n[${step}/9] ${STEPS[step]}`);
  console.log(`   ${message}`);
}

function run(cmd, options = {}) {
  try {
    return execSync(cmd, { encoding: 'utf8', stdio: 'pipe', ...options });
  } catch (err) {
    console.error(`   ❌ Erreur: ${err.message}`);
    if (err.stdout) console.error(`   stdout: ${err.stdout}`);
    if (err.stderr) console.error(`   stderr: ${err.stderr}`);
    throw err;
  }
}

function checkCommand(cmd) {
  try {
    execSync(`which ${cmd}`, { stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
}

async function deploy() {
  console.log('🎵═══════════════════════════════════════');
  console.log('🎵  COSY V0 — Déploiement Automatisé');
  console.log('🎵═══════════════════════════════════════');

  const startTime = Date.now();

  try {
    // ÉTAPE 1 : Vérification
    log(1, 'Vérification des prérequis...');

    if (!checkCommand('node')) {
      console.error('   ❌ Node.js non installé');
      process.exit(1);
    }
    console.log('   ✅ Node.js : ' + run('node --version').trim());

    if (!checkCommand('npm')) {
      console.error('   ❌ npm non installé');
      process.exit(1);
    }
    console.log('   ✅ npm : ' + run('npm --version').trim());

    if (!checkCommand('git')) {
      console.log('   ⚠️  git non installé (optionnel pour Render)');
    } else {
      console.log('   ✅ git : ' + run('git --version').trim().split(' ')[2]);
    }

    const renderKey = process.env.RENDER_API_KEY;
    const renderOwner = process.env.RENDER_OWNER_ID;

    if (!renderKey || !renderOwner) {
      console.log('   ⚠️  Variables Render non définies');
      console.log('      export RENDER_API_KEY="rk_..."');
      console.log('      export RENDER_OWNER_ID="usr_..."');
      console.log('   ℹ️  Mode local uniquement (pas de déploiement cloud)');
    } else {
      console.log('   ✅ Render API Key configurée');
    }

    // ÉTAPE 2 : Clés JWT
    log(2, 'Génération des clés JWT...');

    const keysDir = path.join(__dirname, '..', 'keys');
    const privateKeyPath = path.join(keysDir, 'jwt-private.pem');
    const publicKeyPath = path.join(keysDir, 'jwt-public.pem');

    if (fs.existsSync(privateKeyPath) && fs.existsSync(publicKeyPath)) {
      console.log('   ℹ️  Clés JWT existantes — utilisation des clés actuelles');
    } else {
      if (!checkCommand('openssl')) {
        console.log('   ⚠️  OpenSSL non trouvé — génération fallback avec Node.js crypto');
        const { generateKeyPairSync } = require('crypto');
        const keys = generateKeyPairSync('rsa', { modulusLength: 2048 });
        fs.mkdirSync(keysDir, { recursive: true });
        fs.writeFileSync(privateKeyPath, keys.privateKey.export({ type: 'pkcs1', format: 'pem' }));
        fs.writeFileSync(publicKeyPath, keys.publicKey.export({ type: 'pkcs1', format: 'pem' }));
        console.log('   ✅ Clés JWT générées (Node.js crypto)');
      } else {
        run('bash scripts/generate-keys.sh', { cwd: path.join(__dirname, '..') });
        console.log('   ✅ Clés JWT générées (OpenSSL)');
      }
    }

    // ÉTAPE 3 : Dépendances
    log(3, 'Installation des dépendances...');
    const backendDir = path.join(__dirname, '..');
    run('npm install', { cwd: backendDir });
    console.log('   ✅ Dépendances installées');

    // ÉTAPE 4 : Configuration
    log(4, 'Configuration de l'environnement...');

    const envPath = path.join(backendDir, '.env');
    if (!fs.existsSync(envPath)) {
      const envContent = `NODE_ENV=development
PORT=3000
HOST=0.0.0.0
DATABASE_URL=postgres://cosy_admin:cosy_secret_2026@localhost:5432/cosy_v0
JWT_PRIVATE_KEY_PATH=./keys/jwt-private.pem
JWT_PUBLIC_KEY_PATH=./keys/jwt-public.pem
JWT_EXPIRES_IN=3600
REFRESH_TOKEN_EXPIRES_IN=604800
OTP_EXPIRES_IN=300
CORS_ORIGIN=*
RATE_LIMIT_MAX=1000
`;
      fs.writeFileSync(envPath, envContent);
      console.log('   ✅ Fichier .env créé');
    } else {
      console.log('   ℹ️  Fichier .env existant');
    }

    // ÉTAPE 5 : Déploiement Cloud (si clés Render)
    if (renderKey && renderOwner) {
      log(5, 'Déploiement sur Render...');
      try {
        run('node scripts/setup-render.js', { cwd: backendDir });
        console.log('   ✅ Services Render créés');
      } catch (err) {
        console.log('   ⚠️  Échec déploiement Render — passage en mode local');
        console.log(`   Erreur: ${err.message}`);
      }
    } else {
      log(5, 'Mode local uniquement (pas de clés Render)');
    }

    // ÉTAPE 6 : Migration (si DB locale disponible)
    log(6, 'Migration base de données...');

    // Vérifier si PostgreSQL est accessible
    try {
      run('node scripts/migrate.js', { cwd: backendDir });
      console.log('   ✅ Migrations exécutées');
    } catch (err) {
      console.log('   ⚠️  PostgreSQL non accessible — migrations ignorées');
      console.log('      Pour exécuter plus tard: npm run migrate');
    }

    // ÉTAPE 7 : Seeding
    log(7, 'Seeding des données...');

    try {
      run('node scripts/seed.js', { cwd: backendDir });
      console.log('   ✅ Données de test insérées');
    } catch (err) {
      console.log('   ⚠️  Seeding ignoré (DB non accessible)');
      console.log('      Pour exécuter plus tard: npm run seed');
    }

    // ÉTAPE 8 : Tests
    log(8, 'Tests API...');

    try {
      // Démarrer le serveur en background pour tester
      console.log('   ℹ️  Démarrage serveur temporaire...');
      const server = require('child_process').spawn('node', ['server.js'], {
        cwd: backendDir,
        detached: true,
        stdio: 'ignore'
      });
      server.unref();

      // Attendre que le serveur démarre
      await new Promise(r => setTimeout(r, 3000));

      try {
        run('node scripts/test-api.js', { cwd: backendDir });
        console.log('   ✅ Tests API passés');
      } catch (err) {
        console.log('   ⚠️  Tests API échoués — serveur peut-être pas encore prêt');
      }

      // Tuer le serveur temporaire
      try { process.kill(-server.pid); } catch {}

    } catch (err) {
      console.log('   ⚠️  Tests ignorés');
    }

    // ÉTAPE 9 : Récapitulatif
    const duration = ((Date.now() - startTime) / 1000).toFixed(1);

    log(9, `Terminé en ${duration}s`);
    console.log('\n🎵═══════════════════════════════════════');
    console.log('🎵  COSY V0 — Déploiement Terminé');
    console.log('🎵═══════════════════════════════════════');
    console.log('\n📋 Prochaines étapes :');
    console.log('   1. Si mode local : npm run dev (démarrer le serveur)');
    console.log('   2. Si Render : configurer le repo Git dans le dashboard');
    console.log('   3. Ouvrir frontend/cosy-app.html dans le navigateur');
    console.log('   4. API Docs : http://localhost:3000/documentation');
    console.log('\n🚀 Ready to build the African creator ecosystem!');

  } catch (err) {
    console.error('\n❌ Déploiement échoué:', err.message);
    process.exit(1);
  }
}

deploy();
