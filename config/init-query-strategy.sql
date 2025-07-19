-- Query Strategy Database Initialization (lmw_mvp_query_strategy)
-- No authentication required - using trust authentication

-- ===========================================
-- LEARNER PROFILES AND STRATEGIES
-- ===========================================

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

-- ===========================================
-- INDEXES FOR PERFORMANCE
-- ===========================================

CREATE INDEX IF NOT EXISTS idx_learners_email ON learners(email);
CREATE INDEX IF NOT EXISTS idx_learners_experience_level ON learners(experience_level);
CREATE INDEX IF NOT EXISTS idx_strategies_learner_id ON strategies(learner_id);
CREATE INDEX IF NOT EXISTS idx_strategies_course_id ON strategies(course_id);
CREATE INDEX IF NOT EXISTS idx_decision_logs_learner_id ON decision_logs(learner_id);
CREATE INDEX IF NOT EXISTS idx_decision_logs_timestamp ON decision_logs(timestamp);

COMMIT; 