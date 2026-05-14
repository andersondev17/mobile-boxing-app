-- Initial PostgreSQL setup for boxing-api
-- Run automatically by postgres image via docker-entrypoint-initdb.d

-- Enable UUID extension (used by all primary keys)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Optional: enable pg_trgm for future text search on exercise titles
-- CREATE EXTENSION IF NOT EXISTS "pg_trgm";
