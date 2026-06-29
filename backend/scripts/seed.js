const { Pool } = require('pg');
const { v4: uuidv4 } = require('uuid');
require('dotenv').config();

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

async function seed() {
  const client = await pool.connect();

  try {
    await client.query('BEGIN');
    console.log('🌱 Seeding COSY V0 database...');

    // Users
    const adminId = uuidv4();
    const ccoId = uuidv4();
    const financeId = uuidv4();
    const listenerId = uuidv4();
    const artistUserId = uuidv4();
    const advertiserId = uuidv4();

    await client.query(`INSERT INTO users (id, phone, name, username, role, city, trust_score, onboarding_completed)
      VALUES ($1,$2,$3,$4,$5,$6,$7,$8)`,
      [adminId, '+237600000001', 'Admin COSY', 'admin_cosy', 'admin', 'Douala', 100, true]);

    await client.query(`INSERT INTO users (id, phone, name, username, role, city, trust_score, onboarding_completed)
      VALUES ($1,$2,$3,$4,$5,$6,$7,$8)`,
      [ccoId, '+237600000002', 'Chief Content Officer', 'cco_cosy', 'cco', 'Douala', 95, true]);

    await client.query(`INSERT INTO users (id, phone, name, username, role, city, trust_score, onboarding_completed)
      VALUES ($1,$2,$3,$4,$5,$6,$7,$8)`,
      [financeId, '+237600000003', 'Finance Manager', 'finance_cosy', 'finance', 'Douala', 90, true]);

    await client.query(`INSERT INTO users (id, phone, name, username, role, city, genres, trust_score, onboarding_completed)
      VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)`,
      [listenerId, '+237612345678', 'Aicha Mbarga', 'aicha_m', 'listener', 'Douala', '{"afropop","bikutsi"}', 45, true]);

    await client.query(`INSERT INTO users (id, phone, name, username, role, city, genres, trust_score, onboarding_completed)
      VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)`,
      [artistUserId, '+237699999999', 'Salatiel', 'salatiel_official', 'creator', 'Yaounde',
       '{"afropop","afrobeats"}', 88, true]);

    await client.query(`INSERT INTO users (id, phone, name, username, role, city, onboarding_completed)
      VALUES ($1,$2,$3,$4,$5,$6,$7)`,
      [advertiserId, '+237611111111', 'Jean Brasserie', 'jean_sabc', 'advertiser', 'Douala', true]);

    // Creator
    const creatorId = uuidv4();
    await client.query(`INSERT INTO creators (id, user_id, stage_name, bio, city, genres, verified, status, total_streams, total_revenue, social_links)
      VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)`,
      [creatorId, artistUserId, 'Salatiel', 'Artiste afropop camerounais',
       'Yaounde', '{"afropop","afrobeats"}', true, 'active', 125000, 4500000,
       '{"instagram":"@salatiel","youtube":"SalatielOfficial"}'::jsonb]);

    // Wallet
    await client.query(`INSERT INTO wallets (id, user_id, balance_fcfa, total_earned, total_withdrawn)
      VALUES ($1,$2,$3,$4,$5)`,
      [uuidv4(), artistUserId, 47320, 124700, 77380]);

    // Tracks
    const tracks = [
      { title: 'Bana Mwasi', genre: 'afropop', city: 'Douala', tqs: 82, crs: 91, tss: 67, ccs: 78, status: 'published' },
      { title: 'Mama Douala', genre: 'bikutsi', city: 'Douala', tqs: 72, crs: 88, tss: 34, ccs: 62, status: 'published' },
      { title: 'Douala By Night', genre: 'coupe-decale', city: 'Douala', tqs: 65, crs: 75, tss: 45, ccs: 60, status: 'published' },
      { title: 'Freestyle Yaounde', genre: 'rap', city: 'Yaounde', tqs: 58, crs: 91, tss: 12, ccs: 48, status: 'pending' },
      { title: 'Dance Africa', genre: 'afrobeats', city: 'Abidjan', tqs: 81, crs: 42, tss: 67, ccs: 65, status: 'published' },
      { title: 'Makossa Classic', genre: 'makossa', city: 'Douala', tqs: 90, crs: 95, tss: 55, ccs: 78, status: 'published' },
    ];

    for (const t of tracks) {
      await client.query(`INSERT INTO tracks (id, creator_id, title, artist_display, genre, city, tqs, crs, tss, ccs, status, duration, bpm, published_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)`,
        [uuidv4(), creatorId, t.title, 'Salatiel', t.genre, t.city, t.tqs, t.crs, t.tss, t.ccs, t.status,
         180 + Math.floor(Math.random() * 120), 100 + Math.floor(Math.random() * 40),
         t.status === 'published' ? new Date() : null]);
    }

    // Radios
    const radios = [
      { name: 'Balafon FM', city: 'Douala', stream_url: 'https://stream.balafon.fm/live', listeners: 5000 },
      { name: 'Radio Siantou', city: 'Douala', stream_url: 'https://stream.siantou.fm/live', listeners: 3000 },
      { name: 'Sweet FM', city: 'Douala', stream_url: 'https://stream.sweetfm.cm/live', listeners: 2000 },
    ];

    for (const r of radios) {
      await client.query(`INSERT INTO radios (id, name, city, stream_url, status, current_listeners)
        VALUES ($1,$2,$3,$4,$5,$6)`,
        [uuidv4(), r.name, r.city, r.stream_url, 'active', r.listeners]);
    }

    // Campaign
    await client.query(`INSERT INTO campaigns (id, advertiser_id, name, budget_total, budget_daily, spent, start_date, end_date, target_cities, target_genres, target_age_min, target_age_max, target_hours, format, status)
      VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)`,
      [uuidv4(), advertiserId, 'Promo Album Salatiel', 700000, 50000, 350000,
       '2026-07-01', '2026-07-31', '{"Douala","Yaounde"}', '{"afropop","afrobeats"}',
       18, 35, '{18,19,20,21,22,23}', 'audio_preroll', 'active']);

    // AI Scores
    const trackRows = await client.query('SELECT id FROM tracks WHERE creator_id = $1', [creatorId]);
    for (const row of trackRows.rows) {
      await client.query(`INSERT INTO ai_scores (id, track_id, tqs, crs, tss, ccs, classification, storage_tier, placement, flags, status)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)`,
        [uuidv4(), row.id,
         '{"total":72,"audio":84,"metadata":71,"format":78,"duration":90,"silence":65}'::jsonb,
         '{"total":88,"artist_origin":95,"language":80,"genre":90,"collaboration":70,"geography":85,"platform":80}'::jsonb,
         '{"total":34,"stream_velocity":45,"social_momentum":20,"radio_frequency":30,"search_volume":25,"playlist_adds":15}'::jsonb,
         62,
         '{"genres":["afropop"],"languages":["francais"],"mood":["festif"],"bpm":104,"explicit":false}'::jsonb,
         'warm', 'catalogue_standard', '[]'::jsonb, 'completed']);
    }

    // Moderation queue
    const pending = await client.query("SELECT id FROM tracks WHERE status = 'pending'");
    for (const row of pending.rows) {
      await client.query(`INSERT INTO moderation_queue (id, track_id, status, notes)
        VALUES ($1,$2,$3,$4)`,
        [uuidv4(), row.id, 'pending', 'En attente de review CCO']);
    }

    // Notifications
    await client.query(`INSERT INTO notifications (id, user_id, type, title, body, data, priority)
      VALUES ($1,$2,$3,$4,$5,$6,$7)`,
      [uuidv4(), artistUserId, 'in_app', 'Nouveau record !',
       'Bana Mwasi vient de depasser 25 000 streams',
       '{"track_id":"xxx","screen":"analytics"}'::jsonb, 'high']);

    await client.query('COMMIT');

    console.log('✅ Database seeded successfully!');
    console.log('   • 6 users (admin, cco, finance, artist, listener, advertiser)');
    console.log('   • 1 creator (Salatiel)');
    console.log('   • 6 tracks');
    console.log('   • 3 radios');
    console.log('   • 1 campaign');
    console.log('   • AI scores + moderation queue');

  } catch (err) {
    await client.query('ROLLBACK');
    console.error('❌ Seeding failed:', err.message);
    throw err;
  } finally {
    client.release();
    await pool.end();
  }
}

seed().catch(console.error);
