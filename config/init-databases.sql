-- PostgreSQL Database Initialization for Microservices
-- Creates separate databases and users for each microservice

-- ===========================================
-- CREATE DATABASES
-- ===========================================

-- Course Manager Database
CREATE DATABASE course_manager_db;
CREATE USER course_manager_user WITH PASSWORD 'course_manager_pass';
GRANT ALL PRIVILEGES ON DATABASE course_manager_db TO course_manager_user;

-- Knowledge Graph Metadata Database
CREATE DATABASE kg_metadata_db;
CREATE USER kg_user WITH PASSWORD 'kg_user_pass';
GRANT ALL PRIVILEGES ON DATABASE kg_metadata_db TO kg_user;

-- Query Strategy Database
CREATE DATABASE query_strategy_db;
CREATE USER query_user WITH PASSWORD 'query_user_pass';
GRANT ALL PRIVILEGES ON DATABASE query_strategy_db TO query_user;

-- Query Logs Database
CREATE DATABASE query_logs_db;
CREATE USER query_logs_user WITH PASSWORD 'query_logs_pass';
GRANT ALL PRIVILEGES ON DATABASE query_logs_db TO query_logs_user;

-- PLT Storage Database
CREATE DATABASE plt_storage_db;
CREATE USER plt_user WITH PASSWORD 'plt_user_pass';
GRANT ALL PRIVILEGES ON DATABASE plt_storage_db TO plt_user;

-- System Configuration Database
CREATE DATABASE system_config_db;
CREATE USER system_admin WITH PASSWORD 'system_admin_pass';
GRANT ALL PRIVILEGES ON DATABASE system_config_db TO system_admin;

-- ===========================================
-- INITIALIZE SCHEMAS
-- ===========================================

-- Connect to course_manager_db and create tables
\c course_manager_db;

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

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO course_manager_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO course_manager_user;

-- Connect to kg_metadata_db and create tables
\c kg_metadata_db;

CREATE TABLE IF NOT EXISTS kg_metadata (
    kg_id SERIAL PRIMARY KEY,
    course_id VARCHAR(50),
    version INTEGER,
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

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO kg_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO kg_user;

-- Connect to query_strategy_db and create tables
\c query_strategy_db;

CREATE TABLE IF NOT EXISTS learners (
    learner_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    learning_style VARCHAR(50),
    pace VARCHAR(50),
    experience_level VARCHAR(50),
    preferences JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS strategies (
    strategy_id SERIAL PRIMARY KEY,
    learner_id VARCHAR(50) REFERENCES learners(learner_id),
    course_id VARCHAR(50),
    strategy_type VARCHAR(50), -- recommendation, subgraph, plt_generation
    context JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS decision_logs (
    log_id SERIAL PRIMARY KEY,
    learner_id VARCHAR(50) REFERENCES learners(learner_id),
    course_id VARCHAR(50),
    decision_label VARCHAR(100),
    routing_result VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO query_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO query_user;

-- Connect to query_logs_db and create tables
\c query_logs_db;

CREATE TABLE IF NOT EXISTS query_history (
    query_id SERIAL PRIMARY KEY,
    learner_id VARCHAR(50),
    course_id VARCHAR(50),
    cypher_query TEXT,
    execution_time_ms INTEGER,
    result_count INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS performance_metrics (
    metric_id SERIAL PRIMARY KEY,
    query_type VARCHAR(50),
    avg_execution_time_ms FLOAT,
    total_queries INTEGER,
    success_rate FLOAT,
    date_recorded DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS cached_results (
    cache_id SERIAL PRIMARY KEY,
    query_hash VARCHAR(64),
    query_text TEXT,
    result_data JSONB,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO query_logs_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO query_logs_user;

-- Connect to plt_storage_db and create tables
\c plt_storage_db;

CREATE TABLE IF NOT EXISTS personalized_trees (
    plt_id SERIAL PRIMARY KEY,
    learner_id VARCHAR(50),
    course_id VARCHAR(50),
    tree_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS learning_paths (
    path_id SERIAL PRIMARY KEY,
    plt_id INTEGER REFERENCES personalized_trees(plt_id),
    sequence_order INTEGER,
    learning_objective TEXT,
    knowledge_component TEXT,
    instruction_method TEXT,
    priority VARCHAR(20),
    status VARCHAR(50) DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS progress_tracking (
    progress_id SERIAL PRIMARY KEY,
    path_id INTEGER REFERENCES learning_paths(path_id),
    learner_id VARCHAR(50),
    completed_at TIMESTAMP,
    time_spent INTEGER,
    performance_score DECIMAL(5,2)
);

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO plt_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO plt_user;

-- Connect to system_config_db and create tables
\c system_config_db;

CREATE TABLE IF NOT EXISTS global_config (
    config_id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE,
    config_value JSONB,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feature_flags (
    flag_id SERIAL PRIMARY KEY,
    flag_name VARCHAR(100) UNIQUE,
    enabled BOOLEAN DEFAULT FALSE,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS system_logs (
    log_id SERIAL PRIMARY KEY,
    service_name VARCHAR(100),
    log_level VARCHAR(20),
    message TEXT,
    metadata JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO system_admin;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO system_admin;

-- ===========================================
-- INSERT INITIAL DATA
-- ===========================================

-- Insert default global configuration
INSERT INTO global_config (config_key, config_value, description) VALUES
('llm_model', '"qwen3:4b"', 'Default LLM model for agents'),
('chunk_size', '1000', 'Default chunk size for content processing'),
('chunk_overlap', '100', 'Default chunk overlap for content processing'),
('faculty_approval_required', 'true', 'Whether faculty approval is required for workflows');

-- Insert default feature flags
INSERT INTO feature_flags (flag_name, enabled, description) VALUES
('enable_plt_generation', true, 'Enable personalized learning tree generation'),
('enable_elasticsearch', true, 'Enable Elasticsearch integration'),
('enable_faculty_workflow', true, 'Enable faculty approval workflow'),
('enable_redis_caching', true, 'Enable Redis caching for query results');

COMMIT; 