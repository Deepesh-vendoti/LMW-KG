#!/bin/bash

# Database Setup Script - Works with existing Neo4j and Elasticsearch containers
# Author: LangGraph KG System
# Date: July 2025

echo "🚀 Setting up databases for LangGraph KG System..."

# Function to check if container is running
check_container() {
    if docker ps --format '{{.Names}}' | grep -q "^$1$"; then
        echo "✅ $1 is running"
        return 0
    else
        echo "❌ $1 is not running"
        return 1
    fi
}

# Check existing containers
echo "📋 Checking existing database containers..."
check_container "local-neo4j"
NEO4J_RUNNING=$?

check_container "elasticsearch-rag"
ELASTICSEARCH_RUNNING=$?

# Test connections
echo "🔍 Testing database connections..."

# Test Neo4j
if [ $NEO4J_RUNNING -eq 0 ]; then
    NEO4J_VERSION=$(curl -s http://localhost:7474 | jq -r '.neo4j_version' 2>/dev/null)
    if [ "$NEO4J_VERSION" != "null" ] && [ "$NEO4J_VERSION" != "" ]; then
        echo "✅ Neo4j $NEO4J_VERSION is accessible"
    else
        echo "⚠️  Neo4j container running but not accessible"
    fi
fi

# Test Elasticsearch
if [ $ELASTICSEARCH_RUNNING -eq 0 ]; then
    ES_VERSION=$(curl -s http://localhost:9200 | jq -r '.version.number' 2>/dev/null)
    if [ "$ES_VERSION" != "null" ] && [ "$ES_VERSION" != "" ]; then
        echo "✅ Elasticsearch $ES_VERSION is accessible"
    else
        echo "⚠️  Elasticsearch container running but not accessible"
    fi
fi

# Set up MongoDB if not exists
echo "🍃 Setting up MongoDB..."
if ! check_container "langgraph_mongodb"; then
    echo "📦 Starting MongoDB container..."
    docker run -d \
        --name langgraph_mongodb \
        -p 27017:27017 \
        -v mongodb_data:/data/db \
        mongo:7.0
    
    # Wait for MongoDB to start
    echo "⏳ Waiting for MongoDB to initialize..."
    sleep 10
    
    # Initialize MongoDB
    echo "🔧 Initializing MongoDB collections..."
    docker exec langgraph_mongodb mongosh --quiet --eval "
    db = db.getSiblingDB('langgraph_kg');
    db.createCollection('learner_profiles');
    db.createCollection('personalized_learning_trees');
    db.createCollection('learning_sessions');
    db.createCollection('course_metadata');
    db.createCollection('pdf_documents');
    
    db.learner_profiles.createIndex({ 'learner_id': 1 }, { unique: true });
    db.personalized_learning_trees.createIndex({ 'learner_id': 1, 'course_id': 1 });
    db.learning_sessions.createIndex({ 'session_id': 1 }, { unique: true });
    db.course_metadata.createIndex({ 'course_id': 1 }, { unique: true });
    db.pdf_documents.createIndex({ 'course_id': 1 });
    
    print('MongoDB collections created successfully');
    "
fi

# Set up Redis if not exists
echo "🔴 Setting up Redis..."
if ! check_container "langgraph_redis"; then
    echo "📦 Starting Redis container..."
    docker run -d \
        --name langgraph_redis \
        -p 6379:6379 \
        redis:7.2-alpine
    
    sleep 3
    
    # Test Redis
    if command -v redis-cli &> /dev/null; then
        REDIS_RESPONSE=$(redis-cli ping 2>/dev/null)
        if [ "$REDIS_RESPONSE" = "PONG" ]; then
            echo "✅ Redis is accessible"
        fi
    else
        echo "⚠️  redis-cli not found, but Redis container is running"
    fi
fi

# Set up Elasticsearch indices
echo "� Setting up Elasticsearch indices..."
if [ $ELASTICSEARCH_RUNNING -eq 0 ]; then
    echo "📄 Creating course_content index..."
    curl -X PUT "localhost:9200/course_content" \
        -H 'Content-Type: application/json' \
        -d'{
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            },
            "mappings": {
                "properties": {
                    "course_id": {"type": "keyword"},
                    "chunk_id": {"type": "keyword"},
                    "content": {"type": "text"},
                    "metadata": {"type": "object"},
                    "embeddings": {"type": "dense_vector", "dims": 384},
                    "timestamp": {"type": "date"}
                }
            }
        }' > /dev/null 2>&1
    
    echo "🧠 Creating knowledge_components index..."
    curl -X PUT "localhost:9200/knowledge_components" \
        -H 'Content-Type: application/json' \
        -d'{
            "mappings": {
                "properties": {
                    "kc_id": {"type": "keyword"},
                    "name": {"type": "text"},
                    "description": {"type": "text"},
                    "course_id": {"type": "keyword"},
                    "difficulty": {"type": "keyword"},
                    "type": {"type": "keyword"}
                }
            }
        }' > /dev/null 2>&1
    
    echo "✅ Elasticsearch indices created"
fi

# Set up Neo4j schema
echo "🗂️  Setting up Neo4j schema..."
if [ $NEO4J_RUNNING -eq 0 ]; then
    echo "📝 Creating Neo4j constraints and indexes..."
    
    # Create constraints
    curl -X POST http://localhost:7474/db/neo4j/tx/commit \
        -H "Content-Type: application/json" \
        -d '{
            "statements": [
                {"statement": "CREATE CONSTRAINT IF NOT EXISTS FOR (lo:LearningObjective) REQUIRE lo.id IS UNIQUE"},
                {"statement": "CREATE CONSTRAINT IF NOT EXISTS FOR (kc:KnowledgeComponent) REQUIRE kc.id IS UNIQUE"},
                {"statement": "CREATE CONSTRAINT IF NOT EXISTS FOR (course:Course) REQUIRE course.id IS UNIQUE"},
                {"statement": "CREATE CONSTRAINT IF NOT EXISTS FOR (learner:Learner) REQUIRE learner.id IS UNIQUE"},
                {"statement": "CREATE CONSTRAINT IF NOT EXISTS FOR (plt:PersonalizedLearningTree) REQUIRE plt.id IS UNIQUE"}
            ]
        }' > /dev/null 2>&1
    
    # Create indexes
    curl -X POST http://localhost:7474/db/neo4j/tx/commit \
        -H "Content-Type: application/json" \
        -d '{
            "statements": [
                {"statement": "CREATE INDEX IF NOT EXISTS FOR (lo:LearningObjective) ON (lo.course_id)"},
                {"statement": "CREATE INDEX IF NOT EXISTS FOR (kc:KnowledgeComponent) ON (kc.course_id)"},
                {"statement": "CREATE INDEX IF NOT EXISTS FOR (kc:KnowledgeComponent) ON (kc.name)"},
                {"statement": "CREATE INDEX IF NOT EXISTS FOR (kc:KnowledgeComponent) ON (kc.text)"},
                {"statement": "CREATE INDEX IF NOT EXISTS FOR (plt:PersonalizedLearningTree) ON (plt.learner_id)"},
                {"statement": "CREATE INDEX IF NOT EXISTS FOR (plt:PersonalizedLearningTree) ON (plt.course_id)"}
            ]
        }' > /dev/null 2>&1
    
    echo "✅ Neo4j schema created"
fi

# Final status check
echo ""
echo "🎉 Database setup completed!"
echo "================================="
echo "� Database Status:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(neo4j|elasticsearch|mongodb|redis)"

echo ""
echo "🔗 Database Connections:"
echo "Neo4j Web: http://localhost:7474"
echo "Neo4j Bolt: bolt://localhost:7687"
echo "Elasticsearch: http://localhost:9200"
echo "MongoDB: mongodb://localhost:27017"
echo "Redis: localhost:6379"

echo ""
echo "📚 Next Steps:"
echo "1. Update config/database_connections.yaml with these settings"
echo "2. Test the system: python3 -m orchestrator.main learner --learner_id student123 --course_id cs-101"
echo "3. Process your PDF document using the content pipeline"
echo "4. Check DATABASE_SETUP.md for detailed configuration options"
