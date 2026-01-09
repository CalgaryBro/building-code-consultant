-- Initialize PostgreSQL extensions for Calgary Building Code Expert System

-- Enable vector extension for semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable PostGIS for spatial/geographic data
CREATE EXTENSION IF NOT EXISTS postgis;

-- Enable full-text search utilities
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE calgary_codes TO postgres;
