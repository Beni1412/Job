-- ============================================================
-- AI Career Advisor v2.0 — Supabase Schema
-- Jalankan SQL ini di Supabase SQL Editor
-- ============================================================

-- 1. Tabel Users
CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Tabel User Profiles
CREATE TABLE IF NOT EXISTS user_profiles (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    full_name  TEXT,
    phone      TEXT,
    address    TEXT,
    city       TEXT,
    linkedin   TEXT,
    github     TEXT,
    about_me   TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Tabel User Skills
CREATE TABLE IF NOT EXISTS user_skills (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID REFERENCES users(id) ON DELETE CASCADE,
    skill_name TEXT NOT NULL,
    category   TEXT DEFAULT 'technical',
    level      TEXT DEFAULT 'intermediate',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Tabel Work Experience
CREATE TABLE IF NOT EXISTS user_experience (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    company     TEXT NOT NULL,
    title       TEXT NOT NULL,
    start_date  TEXT,
    end_date    TEXT,
    is_current  BOOLEAN DEFAULT FALSE,
    description TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Tabel Education
CREATE TABLE IF NOT EXISTS user_education (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    institution TEXT NOT NULL,
    degree      TEXT,
    field       TEXT,
    grad_year   TEXT,
    gpa         TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Row Level Security (RLS) — optional tapi disarankan
-- ============================================================
ALTER TABLE users          ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles  ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_skills    ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_experience ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_education ENABLE ROW LEVEL SECURITY;
