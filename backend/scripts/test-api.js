const http = require('http');

const API_URL = process.env.API_URL || 'http://localhost:3000';
const HOST = API_URL.replace('http://', '').replace('https://', '').split(':')[0];
const PORT = API_URL.includes(':') ? API_URL.split(':')[2] || 3000 : 3000;

function request(path, method = 'GET', data = null) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: HOST,
      port: PORT,
      path,
      method,
      headers: { 'Content-Type': 'application/json' }
    };

    const req = http.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try { resolve({ status: res.statusCode, body: JSON.parse(body) }); }
        catch { resolve({ status: res.statusCode, body }); }
      });
    });

    req.on('error', reject);
    if (data) req.write(JSON.stringify(data));
    req.end();
  });
}

async function test() {
  console.log('🧪 Testing COSY API...');
  console.log(`   URL: ${API_URL}\n`);

  const tests = [
    { name: 'Health', path: '/health', method: 'GET' },
    { name: 'Cities', path: '/api/v0/pulse/cities', method: 'GET' },
    { name: 'Trending Douala', path: '/api/v0/pulse/Douala/tracks?period=24h', method: 'GET' },
    { name: 'OTP Request', path: '/api/v0/auth/otp/request', method: 'POST', data: { phone: '+237612345678' } },
    { name: 'Tracks', path: '/api/v0/tracks', method: 'GET' },
    { name: 'Radios', path: '/api/v0/radios', method: 'GET' },
  ];

  let passed = 0;
  let failed = 0;

  for (const t of tests) {
    try {
      const res = await request(t.path, t.method, t.data);
      const ok = res.status >= 200 && res.status < 300;
      console.log(`${ok ? '✅' : '❌'} ${t.name}: ${ok ? 'OK' : 'FAIL'} (${res.status})`);
      if (ok) passed++; else failed++;
    } catch (err) {
      console.log(`❌ ${t.name}: ERROR (${err.message})`);
      failed++;
    }
  }

  console.log(`\n📊 Résultats: ${passed} passés, ${failed} échoués`);
  console.log(failed === 0 ? '🎉 Tous les tests sont passés!' : '⚠️ Certains tests ont échoué');
}

test();
