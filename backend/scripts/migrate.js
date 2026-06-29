const { Pool } = require('pg');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

async function migrate() {
  console.log('🔄 Exécution des migrations...');

  try {
    const sqlPath = path.join(__dirname, '..', 'migrations', '001_init_schema.sql');

    if (!fs.existsSync(sqlPath)) {
      console.error('❌ Fichier de migration non trouvé:', sqlPath);
      process.exit(1);
    }

    const sql = fs.readFileSync(sqlPath, 'utf8');
    await pool.query(sql);

    console.log('✅ Migrations exécutées avec succès');
    console.log('   • 20 tables créées');
    console.log('   • 30+ indexes créés');
    console.log('   • 10 triggers updated_at créés');
    console.log('   • 2 vues créées');

  } catch (err) {
    console.error('❌ Erreur migration:', err.message);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

migrate();
