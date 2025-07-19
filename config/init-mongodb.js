// MongoDB Initialization Script for LMW-MVP System
// Creates databases and collections for Content Subsystem services

print('🚀 Initializing MongoDB for LMW-MVP System...');

// ===============================
// CONTENT PREPROCESSOR DATABASE
// ===============================
print('📚 Setting up lmw_mvp_content_preprocessor...');

db = db.getSiblingDB('lmw_mvp_content_preprocessor');

// Create collections
db.createCollection('documents');
db.createCollection('chunks');
db.createCollection('metadata');
db.createCollection('processing_logs');

// Create indexes for performance
db.documents.createIndex({ 'course_id': 1 });
db.documents.createIndex({ 'upload_type': 1 });
db.documents.createIndex({ 'created_at': -1 });

db.chunks.createIndex({ 'document_id': 1 });
db.chunks.createIndex({ 'course_id': 1 });
db.chunks.createIndex({ 'chunk_id': 1 }, { unique: true });

db.processing_logs.createIndex({ 'document_id': 1 });
db.processing_logs.createIndex({ 'processing_time': -1 });

print('✅ lmw_mvp_content_preprocessor initialized');

// ===============================
// KNOWLEDGE GRAPH GENERATOR DATABASE
// ===============================
print('🗂️ Setting up lmw_mvp_kg_generator...');

db = db.getSiblingDB('lmw_mvp_kg_generator');

// Create collections
db.createCollection('course_snapshots');
db.createCollection('kg_versions');
db.createCollection('export_logs');

// Create indexes for performance
db.course_snapshots.createIndex({ 'created_at': -1 });
db.course_snapshots.createIndex({ 'status': 1 });

db.kg_versions.createIndex({ 'snapshot_id': 1 });
db.kg_versions.createIndex({ 'version': 1 });

db.export_logs.createIndex({ 'snapshot_id': 1 });
db.export_logs.createIndex({ 'exported_at': -1 });

print('✅ lmw_mvp_kg_generator initialized');

// ===============================
// ORCHESTRATOR DATABASE
// ===============================
print('🎯 Setting up lmw_mvp_orchestrator...');

db = db.getSiblingDB('lmw_mvp_orchestrator');

// Create collections for general system use
db.createCollection('learner_profiles');
db.createCollection('personalized_learning_trees');
db.createCollection('learning_sessions');
db.createCollection('session_cache');
db.createCollection('query_cache');

// Create indexes
db.learner_profiles.createIndex({ 'learner_id': 1 }, { unique: true });
db.personalized_learning_trees.createIndex({ 'learner_id': 1, 'course_id': 1 });
db.learning_sessions.createIndex({ 'session_id': 1 }, { unique: true });
db.session_cache.createIndex({ 'session_id': 1 });
db.query_cache.createIndex({ 'query_hash': 1 });

print('✅ lmw_mvp_orchestrator initialized');

// ===============================
// VERIFICATION
// ===============================
print('\n📊 Database Initialization Summary:');
print('=====================================');

// List all databases
db.adminCommand('listDatabases').databases.forEach(function(dbInfo) {
    if (dbInfo.name.includes('lmw_mvp_')) {
        print(`✅ ${dbInfo.name}: ${(dbInfo.sizeOnDisk / 1024 / 1024).toFixed(2)} MB`);
    }
});

print('\n🎉 MongoDB initialization completed successfully!');
print('📝 Available databases:');
print('   - lmw_mvp_content_preprocessor (Content Preprocessor service)');
print('   - lmw_mvp_kg_generator (Knowledge Graph Generator service)');
print('   - lmw_mvp_orchestrator (Universal Orchestrator service)');
