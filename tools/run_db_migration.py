#!/usr/bin/env python3
"""
Database Migration Script

Applies database schema updates to fix issues with PostgreSQL tables
and Neo4j connection configuration.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.database_connections import get_database_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_postgresql_migration():
    """Run PostgreSQL migration script to fix schema issues."""
    try:
        # Get database connection
        db_manager = get_database_manager()
        
        # Read migration SQL
        migration_path = Path(__file__).parent.parent / "config" / "db_migration.sql"
        with open(migration_path, "r") as f:
            migration_sql = f.read()
        
        # Execute migration
        with db_manager.get_postgresql_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(migration_sql)
            conn.commit()
        
        logger.info("✅ PostgreSQL migration completed successfully")
        print("✅ PostgreSQL schema updated successfully")
        return True
    
    except Exception as e:
        logger.error(f"❌ PostgreSQL migration failed: {e}")
        print(f"❌ PostgreSQL migration failed: {e}")
        return False

def fix_neo4j_connection():
    """Test and fix Neo4j connection issues."""
    try:
        # Get database connection
        db_manager = get_database_manager()
        
        # Test Neo4j connection with explicit None authentication
        driver = db_manager.get_neo4j_driver()
        
        # Test connection
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            test_value = result.single()["test"]
            
            if test_value == 1:
                logger.info("✅ Neo4j connection successful")
                print("✅ Neo4j connection successful")
                return True
            else:
                logger.error("❌ Neo4j connection test failed")
                print("❌ Neo4j connection test failed")
                return False
    
    except Exception as e:
        logger.error(f"❌ Neo4j connection failed: {e}")
        print(f"❌ Neo4j connection failed: {e}")
        
        # Provide guidance
        print("\n🔧 Troubleshooting Neo4j connection:")
        print("1. Make sure Neo4j is running")
        print("2. Check connection details in config/neo4j_config.py")
        print("3. If using Docker, ensure Neo4j container is up")
        print("4. Try connecting directly to Neo4j Browser (usually at http://localhost:7474)")
        
        return False

def main():
    """Run all database migrations and fixes."""
    print("\n🔄 Running database migrations and fixes...")
    
    # Run PostgreSQL migration
    print("\n📊 Updating PostgreSQL schema...")
    pg_success = run_postgresql_migration()
    
    # Fix Neo4j connection
    print("\n🔌 Testing Neo4j connection...")
    neo4j_success = fix_neo4j_connection()
    
    # Summary
    print("\n📋 Migration Summary:")
    print(f"PostgreSQL Schema Update: {'✅ Success' if pg_success else '❌ Failed'}")
    print(f"Neo4j Connection Test: {'✅ Success' if neo4j_success else '❌ Failed'}")
    
    if pg_success and neo4j_success:
        print("\n🎉 All migrations completed successfully!")
        print("You can now run the knowledge graph generator without errors.")
    else:
        print("\n⚠️ Some migrations failed. See logs above for details.")

if __name__ == "__main__":
    main() 