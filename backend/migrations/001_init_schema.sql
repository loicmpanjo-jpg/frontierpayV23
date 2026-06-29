-- ============================================
-- COSY V0 — Base de donnees PostgreSQL 15
-- 20 tables, 30+ indexes, triggers updated_at
-- ============================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- 1. USERS & AUTH
-- ============================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(255),
    name VARCHAR(255),
    username VARCHAR(50) UNIQUE,
    role VARCHAR(20) NOT NULL DEFAULT 'listener',
    city VARCHAR(100),
    country VARCHAR(2) DEFAULT 'CM',
    genres TEXT[],
    avatar_url TEXT,
    bio TEXT,
    onboarding_completed BOOLEAN DEFAULT false,
    trust_score INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS otp_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(20) NOT NULL,
    code VARCHAR(6) NOT NULL,
    attempts INT DEFAULT 0,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    device_id VARCHAR(255),
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 2. CREATORS
-- ============================================

CREATE TABLE IF NOT EXISTS creators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    stage_name VARCHAR(255) NOT NULL,
    bio TEXT,
    city VARCHAR(100),
    country VARCHAR(2) DEFAULT 'CM',
    genres TEXT[],
    avatar_url TEXT,
    banner_url TEXT,
    verified BOOLEAN DEFAULT false,
    status VARCHAR(20) DEFAULT 'pending_kyc',
    bank_info JSONB,
    mobile_money_number VARCHAR(20),
    social_links JSONB,
    total_streams BIGINT DEFAULT 0,
    total_revenue BIGINT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS creator_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID REFERENCES creators(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL,
    document_url TEXT NOT NULL,
    selfie_url TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 3. TRACKS & MEDIA
-- ============================================

CREATE TABLE IF NOT EXISTS tracks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID REFERENCES creators(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    artist_display VARCHAR(255) NOT NULL,
    featuring TEXT[],
    album_id UUID,
    genre VARCHAR(50) NOT NULL,
    secondary_genres TEXT[],
    language VARCHAR(50),
    city VARCHAR(100),
    country VARCHAR(2) DEFAULT 'CM',
    duration INT,
    bpm INT,
    musical_key VARCHAR(10),
    mood TEXT[],
    explicit BOOLEAN DEFAULT false,
    lyrics TEXT,
    isrc VARCHAR(20),
    audio_media_id UUID,
    artwork_media_id UUID,
    video_media_id UUID,
    status VARCHAR(20) DEFAULT 'pending',
    tqs INT,
    crs INT,
    tss INT,
    ccs INT,
    storage_tier VARCHAR(10) DEFAULT 'warm',
    placement VARCHAR(50) DEFAULT 'catalogue_standard',
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS media_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'uploading',
    original_url TEXT,
    variants JSONB,
    duration INT,
    bitrate INT,
    sample_rate INT,
    format VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

-- ============================================
-- 4. STREAMING
-- ============================================

CREATE TABLE IF NOT EXISTS stream_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    track_id UUID REFERENCES tracks(id),
    user_id UUID REFERENCES users(id),
    session_id VARCHAR(255),
    duration INT NOT NULL,
    completed BOOLEAN DEFAULT false,
    context VARCHAR(50),
    device VARCHAR(50),
    quality INT,
    city VARCHAR(100),
    country VARCHAR(2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 5. WALLETS & FINANCE
-- ============================================

CREATE TABLE IF NOT EXISTS wallets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    balance_fcfa BIGINT DEFAULT 0,
    total_earned BIGINT DEFAULT 0,
    total_withdrawn BIGINT DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'XAF',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_id UUID REFERENCES wallets(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    amount BIGINT NOT NULL,
    balance_after BIGINT NOT NULL,
    description TEXT,
    track_id UUID,
    campaign_id UUID,
    withdrawal_id UUID,
    status VARCHAR(20) DEFAULT 'completed',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS withdrawals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_id UUID REFERENCES wallets(id) ON DELETE CASCADE,
    creator_id UUID REFERENCES creators(id),
    amount BIGINT NOT NULL,
    method VARCHAR(20) NOT NULL,
    phone_number VARCHAR(20),
    account_name VARCHAR(255),
    fee BIGINT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    transaction_reference VARCHAR(255),
    rejection_reason TEXT,
    requested_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    processed_by UUID REFERENCES users(id)
);

-- ============================================
-- 6. ADS
-- ============================================

CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    advertiser_id UUID REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    budget_total BIGINT NOT NULL,
    budget_daily BIGINT,
    spent BIGINT DEFAULT 0,
    start_date DATE NOT NULL,
    end_date DATE,
    target_cities TEXT[],
    target_genres TEXT[],
    target_age_min INT,
    target_age_max INT,
    target_hours INT[],
    spot_audio_media_id UUID,
    spot_duration INT,
    spot_click_url TEXT,
    format VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending_review',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS impressions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id),
    user_id UUID REFERENCES users(id),
    track_id UUID REFERENCES tracks(id),
    context VARCHAR(50),
    device VARCHAR(50),
    city VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS clicks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id),
    user_id UUID REFERENCES users(id),
    impression_id UUID,
    device VARCHAR(50),
    city VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 7. RADIOS
-- ============================================

CREATE TABLE IF NOT EXISTS radios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    country VARCHAR(2) DEFAULT 'CM',
    stream_url TEXT,
    website TEXT,
    contact_name VARCHAR(255),
    contact_phone VARCHAR(20),
    contact_email VARCHAR(255),
    contract_url TEXT,
    contract_start DATE,
    contract_end DATE,
    status VARCHAR(20) DEFAULT 'pending',
    current_track_id UUID,
    current_listeners INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 8. AI & MODERATION
-- ============================================

CREATE TABLE IF NOT EXISTS ai_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    track_id UUID REFERENCES tracks(id) ON DELETE CASCADE,
    tqs JSONB,
    crs JSONB,
    tss JSONB,
    ccs INT,
    classification JSONB,
    storage_tier VARCHAR(10),
    placement VARCHAR(50),
    flags JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS moderation_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    track_id UUID REFERENCES tracks(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending',
    assigned_to UUID REFERENCES users(id),
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMPTZ,
    placement VARCHAR(50),
    rejection_reason TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 9. NOTIFICATIONS
-- ============================================

CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    body TEXT,
    data JSONB,
    read BOOLEAN DEFAULT false,
    priority VARCHAR(10) DEFAULT 'normal',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 10. PLAYLISTS & FAVORITES
-- ============================================

CREATE TABLE IF NOT EXISTS playlists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    track_ids UUID[],
    cover_url TEXT,
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS favorites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    track_id UUID REFERENCES tracks(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, track_id)
);

CREATE TABLE IF NOT EXISTS listening_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    track_id UUID REFERENCES tracks(id) ON DELETE CASCADE,
    duration INT NOT NULL,
    completed BOOLEAN DEFAULT false,
    context VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- INDEXES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_city ON users(city);
CREATE INDEX IF NOT EXISTS idx_creators_user ON creators(user_id);
CREATE INDEX IF NOT EXISTS idx_creators_status ON creators(status);
CREATE INDEX IF NOT EXISTS idx_creators_city ON creators(city);
CREATE INDEX IF NOT EXISTS idx_tracks_creator ON tracks(creator_id);
CREATE INDEX IF NOT EXISTS idx_tracks_status ON tracks(status);
CREATE INDEX IF NOT EXISTS idx_tracks_genre ON tracks(genre);
CREATE INDEX IF NOT EXISTS idx_tracks_city ON tracks(city);
CREATE INDEX IF NOT EXISTS idx_tracks_published ON tracks(published_at);
CREATE INDEX IF NOT EXISTS idx_stream_logs_track ON stream_logs(track_id);
CREATE INDEX IF NOT EXISTS idx_stream_logs_user ON stream_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_stream_logs_created ON stream_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_stream_logs_city ON stream_logs(city);
CREATE INDEX IF NOT EXISTS idx_transactions_wallet ON transactions(wallet_id);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);
CREATE INDEX IF NOT EXISTS idx_campaigns_advertiser ON campaigns(advertiser_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_impressions_campaign ON impressions(campaign_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(user_id, read);
CREATE INDEX IF NOT EXISTS idx_playlists_user ON playlists(user_id);
CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_history_user ON listening_history(user_id);
CREATE INDEX IF NOT EXISTS idx_moderation_status ON moderation_queue(status);
CREATE INDEX IF NOT EXISTS idx_ai_scores_track ON ai_scores(track_id);

-- ============================================
-- TRIGGERS updated_at
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_creators_updated_at BEFORE UPDATE ON creators
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_tracks_updated_at BEFORE UPDATE ON tracks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_wallets_updated_at BEFORE UPDATE ON wallets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_campaigns_updated_at BEFORE UPDATE ON campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_radios_updated_at BEFORE UPDATE ON radios
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_ai_scores_updated_at BEFORE UPDATE ON ai_scores
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_moderation_updated_at BEFORE UPDATE ON moderation_queue
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_playlists_updated_at BEFORE UPDATE ON playlists
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- VUES
-- ============================================

CREATE OR REPLACE VIEW v_creator_stats AS
SELECT 
    c.id,
    c.stage_name,
    c.total_streams,
    c.total_revenue,
    COUNT(t.id) as track_count,
    COUNT(t.id) FILTER (WHERE t.status = 'published') as published_tracks
FROM creators c
LEFT JOIN tracks t ON t.creator_id = c.id
GROUP BY c.id, c.stage_name, c.total_streams, c.total_revenue;

CREATE OR REPLACE VIEW v_trending_tracks AS
SELECT 
    t.id,
    t.title,
    t.artist_display,
    t.artwork_media_id,
    COUNT(s.id) as stream_count,
    COUNT(DISTINCT s.user_id) as unique_listeners
FROM tracks t
LEFT JOIN stream_logs s ON s.track_id = t.id 
    AND s.created_at > NOW() - INTERVAL '24 hours'
WHERE t.status = 'published'
GROUP BY t.id, t.title, t.artist_display, t.artwork_media_id
ORDER BY stream_count DESC;

SELECT 'COSY V0 database schema created successfully' as status;
