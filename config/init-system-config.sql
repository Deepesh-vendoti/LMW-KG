-- System Configuration Database Initialization (lmw_mvp_system_config)
-- No authentication required - using trust authentication

-- ===========================================
-- GLOBAL CONFIGURATION
-- ===========================================

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

CREATE TABLE IF NOT EXISTS service_health (
    health_id SERIAL PRIMARY KEY,
    service_name VARCHAR(100),
    status VARCHAR(20), -- healthy, degraded, down
    response_time_ms INTEGER,
    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details JSONB
);

-- ===========================================
-- INDEXES FOR PERFORMANCE
-- ===========================================

CREATE INDEX IF NOT EXISTS idx_global_config_key ON global_config(config_key);
CREATE INDEX IF NOT EXISTS idx_feature_flags_name ON feature_flags(flag_name);
CREATE INDEX IF NOT EXISTS idx_system_logs_service ON system_logs(service_name);
CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_service_health_service ON service_health(service_name);
CREATE INDEX IF NOT EXISTS idx_service_health_status ON service_health(status);

-- ===========================================
-- INSERT INITIAL DATA
-- ===========================================

-- Insert default global configuration
INSERT INTO global_config (config_key, config_value, description) VALUES
('llm_model', '"qwen3:4b"', 'Default LLM model for agents'),
('chunk_size', '1000', 'Default chunk size for content processing'),
('chunk_overlap', '100', 'Default chunk overlap for content processing'),
('faculty_approval_required', 'true', 'Whether faculty approval is required for workflows'),
('max_concurrent_queries', '10', 'Maximum concurrent graph queries'),
('cache_ttl_hours', '24', 'Cache time-to-live in hours'),
('enable_elasticsearch', 'true', 'Enable Elasticsearch integration'),
('neo4j_connection_pool', '20', 'Neo4j connection pool size');

-- Insert default feature flags
INSERT INTO feature_flags (flag_name, enabled, description) VALUES
('enable_plt_generation', true, 'Enable personalized learning tree generation'),
('enable_elasticsearch', true, 'Enable Elasticsearch integration'),
('enable_faculty_workflow', true, 'Enable faculty approval workflow'),
('enable_redis_caching', true, 'Enable Redis caching for query results'),
('enable_query_optimization', true, 'Enable query performance optimization'),
('enable_adaptive_learning', true, 'Enable adaptive learning algorithms'),
('enable_real_time_analytics', false, 'Enable real-time analytics dashboard'),
('enable_multi_tenant', false, 'Enable multi-tenant support');

COMMIT; 