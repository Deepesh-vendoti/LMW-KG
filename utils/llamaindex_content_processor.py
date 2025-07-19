"""
LlamaIndex Content Processor - Aligned with SME Subsystem

This module provides LlamaIndex-based document processing that matches the SME subsystem's
Elasticsearch ingestion pipeline for consistency across the system.

Target Index: course_docs_ostep_2025
"""

import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from llama_index.core import (
    Document, 
    VectorStoreIndex, 
    Settings,
    StorageContext
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.elasticsearch import ElasticsearchStore
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import TextNode

logger = logging.getLogger(__name__)

class LlamaIndexContentProcessor:
    """
    LlamaIndex-based content processor aligned with SME subsystem.
    
    Uses the same pipeline as SME team:
    - LlamaIndex for document processing
    - sentence-transformers for embeddings
    - Elasticsearch for storage
    - Target index: course_docs_ostep_2025
    """
    
    def __init__(self, 
                 es_host: str = "localhost",
                 es_port: int = 9200,
                 index_name: str = "course_docs_ostep_2025",
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize LlamaIndex content processor.
        
        Args:
            es_host: Elasticsearch host
            es_port: Elasticsearch port
            index_name: Target Elasticsearch index
            embedding_model: HuggingFace embedding model
        """
        self.es_host = es_host
        self.es_port = es_port
        self.index_name = index_name
        self.embedding_model = embedding_model
        
        # Initialize components
        self._setup_embeddings()
        self._setup_elasticsearch()
        self._setup_node_parser()
        
        logger.info(f"Initialized LlamaIndex processor for index: {index_name}")
    
    def _setup_embeddings(self):
        """Setup HuggingFace embeddings."""
        try:
            self.embed_model = HuggingFaceEmbedding(
                model_name=self.embedding_model
            )
            Settings.embed_model = self.embed_model
            logger.info(f"Embeddings initialized: {self.embedding_model}")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}")
            raise
    
    def _setup_elasticsearch(self):
        """Setup Elasticsearch vector store."""
        try:
            self.vector_store = ElasticsearchStore(
                es_url=f"http://{self.es_host}:{self.es_port}",
                index_name=self.index_name,
                dims=384  # all-MiniLM-L6-v2 embedding dimension
            )
            logger.info(f"Elasticsearch store initialized: {self.es_host}:{self.es_port}")
        except Exception as e:
            logger.error(f"Failed to initialize Elasticsearch store: {e}")
            raise
    
    def _setup_node_parser(self):
        """Setup node parser for chunking."""
        self.node_parser = SentenceSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separator="\n"
        )
        logger.info("Node parser initialized")
    
    def process_pdf(self, file_path: str, course_id: str = None) -> Dict[str, Any]:
        """
        Process PDF document using LlamaIndex pipeline.
        
        Args:
            file_path: Path to PDF file
            course_id: Course identifier for metadata
            
        Returns:
            Processing result with chunks and metadata
        """
        try:
            logger.info(f"Processing PDF: {file_path}")
            
            # Load document
            documents = self._load_documents(file_path)
            
            # Parse into nodes
            nodes = self._parse_nodes(documents, course_id)
            
            # Create vector store index
            storage_context = StorageContext.from_defaults(
                vector_store=self.vector_store
            )
            
            # Build index
            index = VectorStoreIndex(
                nodes,
                storage_context=storage_context,
                embed_model=self.embed_model
            )
            
            # Store in Elasticsearch
            self._store_in_elasticsearch(nodes, course_id)
            
            result = {
                "status": "success",
                "file_path": file_path,
                "course_id": course_id,
                "chunks_processed": len(nodes),
                "index_name": self.index_name,
                "embedding_model": self.embedding_model,
                "processing_info": {
                    "processor": "llamaindex",
                    "timestamp": datetime.now().isoformat(),
                    "chunk_size": 1000,
                    "chunk_overlap": 100
                }
            }
            
            logger.info(f"PDF processing completed: {len(nodes)} chunks")
            return result
            
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "file_path": file_path
            }
    
    def _load_documents(self, file_path: str) -> List[Document]:
        """Load documents from file."""
        try:
            # Use LlamaIndex's document loader
            from llama_index.core.readers import SimpleDirectoryReader
            
            # Create a temporary directory with the file
            temp_dir = Path(file_path).parent
            filename = Path(file_path).name
            
            reader = SimpleDirectoryReader(
                input_dir=str(temp_dir),
                filename_as_id=True,
                required_exts=[".pdf"]
            )
            
            documents = reader.load_data()
            logger.info(f"Loaded {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to load documents: {e}")
            raise
    
    def _parse_nodes(self, documents: List[Document], course_id: str = None) -> List[TextNode]:
        """Parse documents into nodes with metadata."""
        nodes = []
        
        for doc in documents:
            # Parse document into nodes
            doc_nodes = self.node_parser.get_nodes_from_documents([doc])
            
            # Add metadata to each node
            for i, node in enumerate(doc_nodes):
                node.metadata.update({
                    "course_id": course_id,
                    "source": "pdf",
                    "file_path": doc.metadata.get("file_path", ""),
                    "chunk_index": i,
                    "processor": "llamaindex",
                    "processed_at": datetime.now().isoformat()
                })
                nodes.append(node)
        
        logger.info(f"Parsed {len(nodes)} nodes from {len(documents)} documents")
        return nodes
    
    def _store_in_elasticsearch(self, nodes: List[TextNode], course_id: str = None):
        """Store nodes in Elasticsearch."""
        try:
            # The vector store will handle the storage
            # This is done automatically when creating the VectorStoreIndex
            logger.info(f"Stored {len(nodes)} nodes in Elasticsearch index: {self.index_name}")
            
        except Exception as e:
            logger.error(f"Failed to store in Elasticsearch: {e}")
            raise
    
    def query_content(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Query content from Elasticsearch using vector similarity.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of relevant chunks
        """
        try:
            # Use direct Elasticsearch query instead of LlamaIndex retriever
            import requests
            
            # If query is empty, get all documents
            if not query.strip():
                search_body = {
                    "query": {"match_all": {}},
                    "size": top_k
                }
            else:
                # Use text search
                search_body = {
                    "query": {
                        "multi_match": {
                            "query": query,
                            "fields": ["text", "metadata.course_id"]
                        }
                    },
                    "size": top_k
                }
            
            url = f"http://{self.es_host}:{self.es_port}/{self.index_name}/_search"
            response = requests.post(url, json=search_body)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                for hit in data['hits']['hits']:
                    source = hit['_source']
                    results.append({
                        "content": source.get('text', ''),
                        "metadata": source.get('metadata', {}),
                        "score": hit.get('_score', None)
                    })
                return results
            else:
                logger.error(f"Elasticsearch query failed: {response.status_code}")
                return []
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the Elasticsearch index."""
        try:
            import requests
            
            url = f"http://{self.es_host}:{self.es_port}/{self.index_name}/_count"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "index_name": self.index_name,
                    "document_count": data.get("count", 0),
                    "status": "active"
                }
            else:
                return {
                    "index_name": self.index_name,
                    "status": "not_found",
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                "index_name": self.index_name,
                "status": "error",
                "error": str(e)
            }

# Convenience function for integration with existing pipeline
def process_pdf_with_llamaindex(file_path: str, course_id: str = None) -> Dict[str, Any]:
    """
    Convenience function to process PDF using LlamaIndex pipeline.
    
    Args:
        file_path: Path to PDF file
        course_id: Course identifier
        
    Returns:
        Processing result
    """
    processor = LlamaIndexContentProcessor()
    return processor.process_pdf(file_path, course_id) 