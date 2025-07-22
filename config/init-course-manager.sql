-- Course Manager Database Initialization (lmw_mvp_course_manager)
-- No authentication required - using trust authentication

-- ===========================================
-- COURSE MANAGEMENT TABLES
-- ===========================================

CREATE TABLE IF NOT EXISTS courses (
    course_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255),
    faculty_id VARCHAR(50),
    upload_type VARCHAR(50),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS uploads (
    upload_id SERIAL PRIMARY KEY,
    course_id VARCHAR(50) REFERENCES courses(course_id),
    file_path TEXT,
    upload_type VARCHAR(50),
    status VARCHAR(50),
    metadata JSONB,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS faculty (
    faculty_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    department VARCHAR(255),
    permissions JSONB
);

CREATE TABLE IF NOT EXISTS approval_workflows (
    workflow_id SERIAL PRIMARY KEY,
    course_id VARCHAR(50) REFERENCES courses(course_id),
    stage VARCHAR(50),
    status VARCHAR(50),
    faculty_id VARCHAR(50) REFERENCES faculty(faculty_id),
    approved_at TIMESTAMP,
    comments TEXT
);

-- ===========================================
-- KNOWLEDGE GRAPH METADATA TABLES
-- ===========================================

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

-- ===========================================
-- INDEXES FOR PERFORMANCE
-- ===========================================

CREATE INDEX IF NOT EXISTS idx_courses_faculty_id ON courses(faculty_id);
CREATE INDEX IF NOT EXISTS idx_courses_status ON courses(status);
CREATE INDEX IF NOT EXISTS idx_uploads_course_id ON uploads(course_id);
CREATE INDEX IF NOT EXISTS idx_approval_workflows_course_id ON approval_workflows(course_id);
CREATE INDEX IF NOT EXISTS idx_kg_metadata_course_id ON kg_metadata(course_id);
CREATE INDEX IF NOT EXISTS idx_faculty_approvals_kg_id ON faculty_approvals(kg_id);

COMMIT; 