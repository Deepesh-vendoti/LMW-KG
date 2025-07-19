-- Learning Tree Database Initialization (lmw_mvp_learning_tree)
-- No authentication required - using trust authentication

-- ===========================================
-- PERSONALIZED LEARNING TREES
-- ===========================================

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

CREATE TABLE IF NOT EXISTS plt_metadata (
    metadata_id SERIAL PRIMARY KEY,
    plt_id INTEGER REFERENCES personalized_trees(plt_id),
    metadata_key VARCHAR(100),
    metadata_value JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================
-- INDEXES FOR PERFORMANCE
-- ===========================================

CREATE INDEX IF NOT EXISTS idx_personalized_trees_learner_id ON personalized_trees(learner_id);
CREATE INDEX IF NOT EXISTS idx_personalized_trees_course_id ON personalized_trees(course_id);
CREATE INDEX IF NOT EXISTS idx_learning_paths_plt_id ON learning_paths(plt_id);
CREATE INDEX IF NOT EXISTS idx_learning_paths_sequence_order ON learning_paths(sequence_order);
CREATE INDEX IF NOT EXISTS idx_progress_tracking_path_id ON progress_tracking(path_id);
CREATE INDEX IF NOT EXISTS idx_progress_tracking_learner_id ON progress_tracking(learner_id);
CREATE INDEX IF NOT EXISTS idx_plt_metadata_plt_id ON plt_metadata(plt_id);

COMMIT; 