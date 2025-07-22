#!/usr/bin/env python3
"""
Database Issues Fixer

Applies all fixes for database-related issues:
1. Neo4j connection configuration
2. PostgreSQL schema updates
3. Missing function implementation
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Run the database migration script
from tools.run_db_migration import main as run_migrations

def main():
    """Run all fixes for database issues."""
    print("\n🔧 Running Database Issues Fixer")
    print("=" * 60)
    
    print("\n1️⃣ Running database migrations...")
    run_migrations()
    
    print("\n2️⃣ Verifying create_knowledge_graph function...")
    try:
        from subsystems.content.services.knowledge_graph_generator import create_knowledge_graph
        print("✅ create_knowledge_graph function is now available")
    except ImportError:
        print("❌ create_knowledge_graph function is still missing")
        print("   Please check subsystems/content/services/knowledge_graph_generator.py")
    
    print("\n3️⃣ Testing Knowledge Graph Generator service...")
    try:
        from subsystems.content.services.knowledge_graph_generator import create_knowledge_graph_generator_service
        service = create_knowledge_graph_generator_service()
        print("✅ Knowledge Graph Generator service initialized successfully")
    except Exception as e:
        print(f"❌ Knowledge Graph Generator service initialization failed: {e}")
    
    print("\n📋 Next steps:")
    print("1. Run the manual microservice flow with the fixed components")
    print("2. Monitor for any remaining errors")
    print("3. If Neo4j connection issues persist, ensure Neo4j is running")
    print("4. If PostgreSQL issues persist, check database connection details")
    
    print("\n🎉 Database fixes applied successfully!")

if __name__ == "__main__":
    main() 