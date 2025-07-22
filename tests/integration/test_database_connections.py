#!/usr/bin/env python3
"""
Database Connection Test Script for LangGraph Knowledge Graph System

Tests all database connections required by the Content Subsystem:
- Neo4j: Knowledge graph storage
- MongoDB: Document storage and metadata
- PostgreSQL: Structured data and faculty approvals
- Redis: Caching and session management
- Elasticsearch: Content search and indexing
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

def test_database_connections():
    """Test all database connections for the Content Subsystem."""
    
    print("🔍 Testing Database Connections for Content Subsystem")
    print("=" * 60)
    
    try:
        from utils.database_connections import get_database_manager
        
        # Get database manager
        db_manager = get_database_manager()
        
        # Test all connections
        health_status = db_manager.check_all_connections()
        
        print("\n📊 Database Health Status:")
        print("-" * 30)
        
        all_healthy = True
        for db_name, is_healthy in health_status.items():
            status_icon = "✅" if is_healthy else "❌"
            print(f"{status_icon} {db_name.upper()}: {'Connected' if is_healthy else 'Failed'}")
            if not is_healthy:
                all_healthy = False
        
        if all_healthy:
            print("\n🎉 All database connections are healthy!")
            return True
        else:
            print("\n⚠️ Some database connections failed. Check the logs above.")
            return False
            
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

def test_content_subsystem_services():
    """Test Content Subsystem services with real database connections."""
    
    print("\n🧪 Testing Content Subsystem Services")
    print("=" * 50)
    
    try:
        from orchestrator.universal_orchestrator import run_cross_subsystem_workflow
        from orchestrator.state import SubsystemType
        
        # Test Content Preprocessor
        print("\n📚 Testing Content Preprocessor...")
        result = run_cross_subsystem_workflow(
            SubsystemType.CONTENT,
            course_id="TEST_COURSE_DB",
            upload_type="elasticsearch",
            es_index="advanced_docs_elasticsearch_v2"
        )
        
        # Check if service completed successfully
        service_statuses = result.get("service_statuses", {})
        content_preprocessor_status = service_statuses.get("content_preprocessor")
        
        if content_preprocessor_status == "completed":
            print("✅ Content Preprocessor: Working with real database connections")
            
            # Check if data was stored
            chunks = result.get("chunks", [])
            print(f"   📄 Processed {len(chunks)} chunks")
            
            content_metadata = result.get("content_metadata", {})
            print(f"   📊 Metadata: {content_metadata.get('total_content_length', 0)} characters")
            
        else:
            print("❌ Content Preprocessor: Failed or not completed")
            return False
        
        # Test Course Manager
        print("\n📋 Testing Course Manager...")
        course_manager_status = service_statuses.get("course_manager")
        
        if course_manager_status == "completed":
            print("✅ Course Manager: Working with real PostgreSQL connections")
            
            course_result = result.get("course_manager_result", {})
            print(f"   🎓 Course: {course_result.get('course_initialized', {}).get('course_id', 'Unknown')}")
            
        else:
            print("❌ Course Manager: Failed or not completed")
            return False
        
        # Test Knowledge Graph Generator (if FCCS is available)
        if result.get("fccs"):
            print("\n🗂️ Testing Knowledge Graph Generator...")
            kg_generator_status = service_statuses.get("knowledge_graph_generator")
            
            if kg_generator_status == "completed":
                print("✅ Knowledge Graph Generator: Working with real multi-database connections")
                
                kg_result = result.get("knowledge_graph_generator_result", {})
                storage_results = kg_result.get("storage_results", {})
                
                for db_name, storage_result in storage_results.items():
                    status = storage_result.get("status", "unknown")
                    status_icon = "✅" if status == "success" else "❌"
                    print(f"   {status_icon} {db_name.upper()}: {status}")
                    
            else:
                print("❌ Knowledge Graph Generator: Failed or not completed")
                return False
        
        print("\n🎉 All Content Subsystem services tested successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Content Subsystem test failed: {e}")
        return False

def test_database_operations():
    """Test specific database operations for each service."""
    
    print("\n🔧 Testing Database Operations")
    print("=" * 40)
    
    try:
        from utils.database_connections import get_database_manager
        
        db_manager = get_database_manager()
        
        # Test Neo4j operations
        print("\n🟢 Testing Neo4j operations...")
        with db_manager.neo4j_session() as session:
            # Test basic query
            result = session.run("MATCH (n) RETURN count(n) as nodeCount")
            node_count = result.single()["nodeCount"]
            print(f"   📊 Total nodes in graph: {node_count}")
            
            # Test constraint creation
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (lo:LearningObjective) REQUIRE lo.id IS UNIQUE")
            print("   🔒 Constraints created/verified")
        
        # Test MongoDB operations
        print("\n🟡 Testing MongoDB operations...")
        db = db_manager.get_mongodb_database('content_preprocessor_db')
        
        # Test collection access
        collections = db.list_collection_names()
        print(f"   📚 Available collections: {', '.join(collections)}")
        
        # Test document insertion
        test_doc = {"test": "data", "timestamp": time.time()}
        result = db.documents.insert_one(test_doc)
        print(f"   📝 Test document inserted: {result.inserted_id}")
        
        # Clean up test document
        db.documents.delete_one({"_id": result.inserted_id})
        print("   🧹 Test document cleaned up")
        
        # Test PostgreSQL operations
        print("\n🔵 Testing PostgreSQL operations...")
        with db_manager.postgresql_cursor() as cursor:
            # Test basic query
            cursor.execute("SELECT version()")
            version = cursor.fetchone()["version"]
            print(f"   🗄️ PostgreSQL version: {version.split(',')[0]}")
            
            # Test table access
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [row["table_name"] for row in cursor.fetchall()]
            print(f"   📋 Available tables: {', '.join(tables)}")
        
        # Test Redis operations
        print("\n🔴 Testing Redis operations...")
        redis_client = db_manager.get_redis_client()
        
        # Test basic operations
        redis_client.set("test_key", "test_value", ex=60)
        value = redis_client.get("test_key")
        print(f"   💾 Redis test: {value}")
        
        # Clean up
        redis_client.delete("test_key")
        
        # Test Elasticsearch operations
        print("\n🟠 Testing Elasticsearch operations...")
        es_client = db_manager.get_elasticsearch_client()
        
        # Test cluster info
        cluster_info = es_client.info()
        version = cluster_info["version"]["number"]
        print(f"   🔍 Elasticsearch version: {version}")
        
        # Test index operations
        indices = es_client.cat.indices(format="json")
        index_names = [index["index"] for index in indices]
        print(f"   📇 Available indices: {', '.join(index_names)}")
        
        print("\n✅ All database operations tested successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database operations test failed: {e}")
        return False

def main():
    """Main test function."""
    
    print("🚀 LangGraph Knowledge Graph System - Database Connection Tests")
    print("=" * 70)
    
    # Test 1: Database connections
    connections_ok = test_database_connections()
    
    if not connections_ok:
        print("\n❌ Database connections failed. Please check your Docker containers.")
        print("💡 Run: docker-compose -f deployment/docker-compose-databases.yml up -d")
        return False
    
    # Test 2: Database operations
    operations_ok = test_database_operations()
    
    if not operations_ok:
        print("\n❌ Database operations failed. Please check your database setup.")
        return False
    
    # Test 3: Content Subsystem services
    services_ok = test_content_subsystem_services()
    
    if not services_ok:
        print("\n❌ Content Subsystem services failed. Please check your service configuration.")
        return False
    
    print("\n🎉 ALL TESTS PASSED!")
    print("=" * 30)
    print("✅ Database connections: Working")
    print("✅ Database operations: Working")
    print("✅ Content Subsystem services: Working")
    print("\n🚀 Your Content Subsystem is ready for production deployment!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 