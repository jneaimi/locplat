-- =============================================================================
-- LocPlat Database Initialization Script
-- =============================================================================

-- Create database extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for common queries
-- (Add your application-specific indexes here)

-- Set database configurations for performance
ALTER DATABASE locplat_production SET log_statement = 'all';
ALTER DATABASE locplat_production SET log_min_duration_statement = 1000;

-- Create any initial data or configuration tables
-- (Add your application-specific initialization here)

-- Example: Create a simple health check table
CREATE TABLE IF NOT EXISTS health_check (
    id SERIAL PRIMARY KEY,
    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'healthy'
);

INSERT INTO health_check (status) VALUES ('initialized') 
ON CONFLICT DO NOTHING;