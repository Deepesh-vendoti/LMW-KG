"""
Database Connection Utilities for LangGraph Knowledge Graph System

Provides real database connections for all Content Subsystem services:
- Neo4j: Knowledge graph storage
- MongoDB: Document storage and metadata
- PostgreSQL: Structured data and faculty approvals
- Redis: Caching and session management
- Elasticsearch: Content search and indexing
"""

import os
import logging
from typing import Dict, Any, Optional
from contextlib import contextmanager

# Database drivers
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logging.warning("Neo4j driver not available. Install with: pip install neo4j")

try:
    import pymongo
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    logging.warning("MongoDB driver not available. Install with: pip install pymongo")

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False
    logging.warning("PostgreSQL driver not available. Install with: pip install psycopg2-binary")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis driver not available. Install with: pip install redis")

try:
    from elasticsearch import Elasticsearch
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False
    logging.warning("Elasticsearch driver not available. Install with: pip install elasticsearch")

from config.loader import config

logger = logging.getLogger(__name__)

class DatabaseConnectionManager:
    """Manages database connections for all Content Subsystem services."""
    
    def __init__(self):
        self._neo4j_driver = None
        self._mongodb_client = None
        self._postgresql_pool = None
        self._redis_client = None
        self._elasticsearch_client = None
        
        # Load database configurations
        self.neo4j_config = config.get_database_config('neo4j')
        self.mongodb_config = config.get_database_config('mongodb')
        self.postgresql_config = config.get_database_config('postgresql')
        self.redis_config = config.get_database_config('redis')
        self.elasticsearch_config = config.get_database_config('elasticsearch')
    
    # ===============================
    # NEO4J CONNECTIONS
    # ===============================
    
    def get_neo4j_driver(self, instance='course_mapper'):
        """Get Neo4j driver instance for specific microservice."""
        if not NEO4J_AVAILABLE:
            raise RuntimeError("Neo4j driver not available")
        
        # Configure ports based on instance using new nested structure
        if instance == 'course_mapper':
            instance_config = self.neo4j_config.get('course_mapper', {})
            uri = instance_config.get('uri', 'bolt://localhost:7687')
            auth_config = instance_config.get('auth', 'none')
        elif instance == 'kli_app':
            instance_config = self.neo4j_config.get('kli_app', {})
            uri = instance_config.get('uri', 'bolt://localhost:7688')
            auth_config = instance_config.get('auth', 'none')
        else:
            instance_config = self.neo4j_config.get('course_mapper', {})
            uri = instance_config.get('uri', 'bolt://localhost:7687')
            auth_config = instance_config.get('auth', 'none')
        
        # Handle "none" authentication consistently
        if auth_config == "none" or auth_config is None:
            # For Neo4j with no auth, we need to use empty tuple
            auth = ("", "")
        else:
            auth = auth_config
        
        try:
            driver = GraphDatabase.driver(uri, auth=auth)
            # Test connection
            with driver.session() as session:
                session.run("RETURN 1")
            logger.info(f"✅ Neo4j connection established for {instance}")
            return driver
        except Exception as e:
            logger.error(f"❌ Neo4j connection failed for {instance}: {e}")
            raise
    
    @contextmanager
    def neo4j_session(self, instance='course_mapper'):
        """Context manager for Neo4j sessions."""
        driver = self.get_neo4j_driver(instance)
        session = driver.session()
        try:
            yield session
        finally:
            session.close()
    
    # ===============================
    # MONGODB CONNECTIONS
    # ===============================
    
    def get_mongodb_client(self):
        """Get MongoDB client instance."""
        if not MONGODB_AVAILABLE:
            raise RuntimeError("MongoDB driver not available")
        
        if self._mongodb_client is None:
            # Use the new nested configuration structure
            content_config = self.mongodb_config.get('content_preprocessor', {})
            uri = content_config.get('uri', 'mongodb://localhost:27017')
            auth_config = content_config.get('auth', 'none')
            
            try:
                # MongoDB with no authentication
                self._mongodb_client = pymongo.MongoClient(uri)
                # Test connection
                self._mongodb_client.admin.command('ping')
                logger.info("✅ MongoDB connection established")
            except Exception as e:
                logger.error(f"❌ MongoDB connection failed: {e}")
                raise
        
        return self._mongodb_client
    
    def get_mongodb_database(self, database_name: Optional[str] = None):
        """Get MongoDB database instance."""
        client = self.get_mongodb_client()
        db_name = database_name or self.mongodb_config.get('database', 'lmw_mvp_content_preprocessor')
        return client[db_name]
    
    # ===============================
    # POSTGRESQL CONNECTIONS
    # ===============================
    
    def get_postgresql_connection(self, database_name=None):
        """Get PostgreSQL connection."""
        if not POSTGRESQL_AVAILABLE:
            raise RuntimeError("PostgreSQL driver not available")
        
        # Use the new nested configuration structure
        if database_name:
            # Get specific database config
            db_config = self.postgresql_config.get(database_name, {})
            host = db_config.get('host', 'localhost')
            port = db_config.get('port', 5432)
            database = db_config.get('database', database_name)
            user = db_config.get('user', 'none')
            password = db_config.get('password', 'none')
        else:
            # Default to course_manager
            db_config = self.postgresql_config.get('course_manager', {})
            host = db_config.get('host', 'localhost')
            port = db_config.get('port', 5432)
            database = db_config.get('database', 'lmw_mvp_course_manager')
            user = db_config.get('user', 'none')
            password = db_config.get('password', 'none')
        
        try:
            # Build connection parameters, omitting user/password if "none"
            conn_params = {
                'host': host,
                'port': port,
                'database': database
            }
            if user and user != "none":
                conn_params['user'] = user
            if password and password != "none":
                conn_params['password'] = password
            
            conn = psycopg2.connect(**conn_params)
            logger.info(f"✅ PostgreSQL connection established to {database}")
            return conn
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection failed to {database}: {e}")
            raise
    
    @contextmanager
    def postgresql_cursor(self):
        """Context manager for PostgreSQL cursors."""
        conn = self.get_postgresql_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()
    
    # ===============================
    # REDIS CONNECTIONS
    # ===============================
    
    def get_redis_client(self, db: int = 0):
        """Get Redis client instance."""
        if not REDIS_AVAILABLE:
            raise RuntimeError("Redis driver not available")
        
        # Use the new nested configuration structure
        cache_config = self.redis_config.get('orchestrator_cache', {})
        host = cache_config.get('host', 'localhost')
        port = cache_config.get('port', 6379)
        auth_config = cache_config.get('auth', 'none')
        
        try:
            # Redis with no authentication
            client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True
            )
            # Test connection
            client.ping()
            logger.info("✅ Redis connection established")
            return client
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise
    
    # ===============================
    # ELASTICSEARCH CONNECTIONS
    # ===============================
    
    def get_elasticsearch_client(self):
        """Get Elasticsearch client instance."""
        if not ELASTICSEARCH_AVAILABLE:
            raise RuntimeError("Elasticsearch driver not available")
        
        if self._elasticsearch_client is None:
            endpoint = self.elasticsearch_config.get('endpoint', 'http://localhost:9200')
            auth_config = self.elasticsearch_config.get('auth', 'none')
            
            try:
                # Elasticsearch with no authentication
                self._elasticsearch_client = Elasticsearch([endpoint])
                # Test connection
                if self._elasticsearch_client.ping():
                    logger.info("✅ Elasticsearch connection established")
                else:
                    raise Exception("Elasticsearch ping failed")
            except Exception as e:
                logger.error(f"❌ Elasticsearch connection failed: {e}")
                raise
        
        return self._elasticsearch_client
    
    # ===============================
    # CONTENT SUBSYSTEM SPECIFIC CONNECTIONS
    # ===============================
    
    def get_course_manager_db(self):
        """Get Course Manager PostgreSQL database."""
        return self.get_postgresql_connection()
    
    def get_content_preprocessor_db(self):
        """Get Content Preprocessor MongoDB database."""
        return self.get_mongodb_database('lmw_mvp_content_preprocessor')
    
    def get_course_content_mapper_db(self):
        """Get Course Content Mapper Neo4j database."""
        return self.get_neo4j_driver('course_mapper')
    
    def get_kli_application_db(self):
        """Get KLI Application Neo4j database."""
        return self.get_neo4j_driver('kli_app')
    
    def get_knowledge_graph_generator_dbs(self):
        """Get Knowledge Graph Generator multi-database connections."""
        return {
            'neo4j_course_mapper': self.get_neo4j_driver('course_mapper'),
            'neo4j_kli_app': self.get_neo4j_driver('kli_app'),
            'mongodb': self.get_mongodb_database('lmw_mvp_kg_generator'),
            'postgresql': self.get_postgresql_connection()
        }
    
    def get_orchestrator_db(self):
        """Get Universal Orchestrator MongoDB database."""
        return self.get_mongodb_database('lmw_mvp_orchestrator')
    
    def get_orchestrator_state_store(self):
        """Get Universal Orchestrator State Store MongoDB database."""
        return self.get_mongodb_database('lmw_mvp_orchestrator')
    
    def get_orchestrator_session_cache(self):
        """Get Universal Orchestrator Session Cache Redis database."""
        return self.get_redis_client()
    
    # ===============================
    # LEARNER SUBSYSTEM SPECIFIC CONNECTIONS
    # ===============================
    
    def get_query_strategy_db(self):
        """Get Query Strategy Manager PostgreSQL database."""
        return self.get_postgresql_connection('lmw_mvp_query_strategy')
    
    def get_graph_query_db(self):
        """Get Graph Query Engine PostgreSQL database."""
        return self.get_postgresql_connection('lmw_mvp_graph_query')
    
    def get_learning_tree_db(self):
        """Get Learning Tree Handler PostgreSQL database."""
        return self.get_postgresql_connection('lmw_mvp_learning_tree')
    
    def get_system_config_db(self):
        """Get System Configuration PostgreSQL database."""
        return self.get_postgresql_connection('lmw_mvp_system_config')
    
    # ===============================
    # HEALTH CHECKS
    # ===============================
    
    def check_all_connections(self) -> Dict[str, bool]:
        """Check health of all database connections."""
        health_status = {}
        
        try:
            # Test Neo4j Course Mapper
            with self.neo4j_session('course_mapper') as session:
                session.run("RETURN 1")
            health_status['neo4j_course_mapper'] = True
        except Exception as e:
            logger.error(f"Neo4j Course Mapper health check failed: {e}")
            health_status['neo4j_course_mapper'] = False
        
        try:
            # Test Neo4j KLI App
            with self.neo4j_session('kli_app') as session:
                session.run("RETURN 1")
            health_status['neo4j_kli_app'] = True
        except Exception as e:
            logger.error(f"Neo4j KLI App health check failed: {e}")
            health_status['neo4j_kli_app'] = False
        
        try:
            # Test MongoDB
            client = self.get_mongodb_client()
            client.admin.command('ping')
            health_status['mongodb'] = True
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            health_status['mongodb'] = False
        
        try:
            # Test PostgreSQL
            with self.postgresql_cursor() as cursor:
                cursor.execute("SELECT 1")
            health_status['postgresql'] = True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            health_status['postgresql'] = False
        
        try:
            # Test Redis
            redis_client = self.get_redis_client()
            redis_client.ping()
            health_status['redis'] = True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            health_status['redis'] = False
        
        try:
            # Test Elasticsearch
            es_client = self.get_elasticsearch_client()
            if es_client.ping():
                health_status['elasticsearch'] = True
            else:
                health_status['elasticsearch'] = False
        except Exception as e:
            logger.error(f"Elasticsearch health check failed: {e}")
            health_status['elasticsearch'] = False
        
        return health_status
    
    # ===============================
    # CLEANUP
    # ===============================
    
    def close_all_connections(self):
        """Close all database connections."""
        # Note: Neo4j drivers are created per instance, so they're managed separately
        # Each driver should be closed by the calling code
        
        if self._mongodb_client:
            self._mongodb_client.close()
            self._mongodb_client = None
        
        if self._elasticsearch_client:
            self._elasticsearch_client.close()
            self._elasticsearch_client = None
        
        logger.info("All database connections closed")

# Global database connection manager instance
_db_manager = None

def get_database_manager() -> DatabaseConnectionManager:
    """Get the global database connection manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseConnectionManager()
    return _db_manager

def close_database_connections():
    """Close all database connections."""
    global _db_manager
    if _db_manager:
        _db_manager.close_all_connections()
        _db_manager = None 