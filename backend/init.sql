-- Auto-run on first container start.
-- Enables PostGIS and creates the initial seed business + API key.

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Seed: demo business (api_key used in .env for local dev)
-- In production, hash the api_key and verify server-side.
INSERT INTO businesses (name, api_key, subscription_tier)
VALUES ('Demo Distributor', 'demo-key', 'pro')
ON CONFLICT DO NOTHING;
