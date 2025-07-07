-- Kormányzati Külgazdasági Szemle Database Initialization

-- Create database (if not exists via environment)
-- CREATE DATABASE IF NOT EXISTS gazdhirlevel;

-- Connect to the database
\c gazdhirlevel;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant permissions to user
GRANT ALL PRIVILEGES ON DATABASE gazdhirlevel TO gazdhir_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO gazdhir_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO gazdhir_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO gazdhir_user;

-- Default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO gazdhir_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO gazdhir_user;