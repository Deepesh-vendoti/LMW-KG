-- Graph Query Database Initialization (lmw_mvp_graph_query)
-- No authentication required - using trust authentication

-- ===========================================
-- QUERY PERFORMANCE AND LOGS
-- ===========================================

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

CREATE TABLE IF NOT EXISTS query_patterns (
    pattern_id SERIAL PRIMARY KEY,
    pattern_name VARCHAR(100),
    cypher_template TEXT,
    parameters JSONB,
    usage_count INTEGER DEFAULT 0,
    avg_performance_ms FLOAT,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================
-- INDEXES FOR PERFORMANCE
-- ===========================================

CREATE INDEX IF NOT EXISTS idx_query_history_learner_id ON query_history(learner_id);
CREATE INDEX IF NOT EXISTS idx_query_history_course_id ON query_history(course_id);
CREATE INDEX IF NOT EXISTS idx_query_history_timestamp ON query_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_cached_results_query_hash ON cached_results(query_hash);
CREATE INDEX IF NOT EXISTS idx_cached_results_expires_at ON cached_results(expires_at);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_date ON performance_metrics(date_recorded);

COMMIT; 