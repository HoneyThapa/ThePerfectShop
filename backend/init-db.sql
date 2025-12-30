-- Initialize ThePerfectShop database
-- This script runs when the PostgreSQL container starts for the first time

-- Create extensions if they don't exist
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create application user (if not using default)
-- DO $$ 
-- BEGIN
--     IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'theperfectshop_app') THEN
--         CREATE ROLE theperfectshop_app WITH LOGIN PASSWORD 'app_password';
--     END IF;
-- END
-- $$;

-- Grant necessary permissions
-- GRANT CONNECT ON DATABASE theperfectshop TO theperfectshop_app;
-- GRANT USAGE ON SCHEMA public TO theperfectshop_app;
-- GRANT CREATE ON SCHEMA public TO theperfectshop_app;

-- Create indexes for performance (these will be created by Alembic migrations)
-- But we can add some basic ones here for immediate use

-- Performance monitoring view
CREATE OR REPLACE VIEW db_performance_stats AS
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE schemaname = 'public'
ORDER BY tablename, attname;

-- Log successful initialization
INSERT INTO pg_stat_statements_info (dealloc) VALUES (0) ON CONFLICT DO NOTHING;

-- Create a simple health check function
CREATE OR REPLACE FUNCTION health_check() 
RETURNS TABLE(status text, timestamp timestamptz) 
LANGUAGE sql 
AS $$
    SELECT 'healthy'::text, now()::timestamptz;
$$;