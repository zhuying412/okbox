-- PostgreSQL initialization script
-- This runs on first container creation only

-- Enable useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create audit schema for separation of concerns
CREATE SCHEMA IF NOT EXISTS audit;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA audit TO okbox;
