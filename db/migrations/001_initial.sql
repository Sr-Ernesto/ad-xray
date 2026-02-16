-- Initial Schema

CREATE TABLE IF NOT EXISTS scrape_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    country TEXT DEFAULT 'CO',
    max_count INT DEFAULT 20,
    status TEXT DEFAULT 'pending',    -- pending, running, completed, failed
    ads_found INT DEFAULT 0,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS ads (
    id BIGINT PRIMARY KEY,              -- ad_archive_id de Meta
    ad_id_internal TEXT,
    page_name TEXT,
    page_id TEXT,
    page_profile_uri TEXT,
    page_profile_picture_url TEXT,
    page_like_count INT,
    page_categories TEXT[],
    
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT true,
    
    body_text TEXT,
    title TEXT,
    cta TEXT,
    cta_type TEXT,
    link_url TEXT,
    link_description TEXT,
    
    publisher_platform TEXT[],
    byline TEXT,
    
    image_url TEXT,
    video_url TEXT,
    card_count INT DEFAULT 0,
    s3_link TEXT,
    
    -- Inspector results
    funnel_type TEXT,           -- 'cod', 'hotmart', 'whatsapp', 'shopify', 'unknown'
    funnel_confidence FLOAT,
    funnel_signals JSONB,      -- {"cod_keywords": [...], "whatsapp_found": true, ...}
    landing_page_url TEXT,     -- URL final después de redirects
    
    -- AI Analysis
    ai_analysis JSONB,
    
    -- Meta
    country TEXT,
    query TEXT,
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    job_id UUID REFERENCES scrape_jobs(id)
);

CREATE TABLE IF NOT EXISTS competitors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id TEXT UNIQUE NOT NULL,
    page_name TEXT,
    category TEXT,
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_ads_page_id ON ads(page_id);
CREATE INDEX IF NOT EXISTS idx_ads_country ON ads(country);
CREATE INDEX IF NOT EXISTS idx_ads_funnel_type ON ads(funnel_type);
CREATE INDEX IF NOT EXISTS idx_ads_scraped_at ON ads(scraped_at);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON scrape_jobs(status);
