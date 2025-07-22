-- Database Migration Script
-- Fixes schema discrepancies and ensures compatibility with code

-- Add missing status column to kg_metadata if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'kg_metadata' AND column_name = 'status'
    ) THEN
        ALTER TABLE kg_metadata ADD COLUMN status VARCHAR(50);
    END IF;
END $$;

-- Update any existing rows to have a default status
UPDATE kg_metadata SET status = 'active' WHERE status IS NULL;

-- Ensure all required tables exist
CREATE TABLE IF NOT EXISTS kg_metadata (
    kg_id SERIAL PRIMARY KEY,
    course_id VARCHAR(50),
    version INTEGER,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    neo4j_nodes_count INTEGER,
    neo4j_relationships_count INTEGER,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS version_control (
    version_id SERIAL PRIMARY KEY,
    kg_id INTEGER REFERENCES kg_metadata(kg_id),
    changes JSONB,
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS faculty_approvals (
    approval_id SERIAL PRIMARY KEY,
    kg_id INTEGER REFERENCES kg_metadata(kg_id),
    stage VARCHAR(10), -- FACD, FCCS, FFCS
    faculty_id VARCHAR(50),
    approved BOOLEAN DEFAULT FALSE,
    approved_at TIMESTAMP,
    comments TEXT
);

-- Create a function to safely update the PostgreSQL storage in knowledge_graph_generator.py
CREATE OR REPLACE FUNCTION store_kg_metadata(
    p_kg_id TEXT,
    p_course_id TEXT,
    p_version TEXT,
    p_status TEXT
) RETURNS BOOLEAN AS $$
BEGIN
    INSERT INTO kg_metadata (kg_id, course_id, version, status, created_at)
    VALUES (p_kg_id, p_course_id, p_version, p_status, CURRENT_TIMESTAMP);
    RETURN TRUE;
EXCEPTION WHEN OTHERS THEN
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql; 