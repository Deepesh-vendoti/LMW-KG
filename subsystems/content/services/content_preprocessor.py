"""
Content Preprocessor Microservice

Handles file upload, chunking, and metadata extraction.
Processes various content types and prepares them for agent processing.
"""

from typing import Dict, Any, List
import json
import logging
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from orchestrator.state import SubsystemType, UniversalState
from config.loader import get_chunk_settings
from utils.logging import get_content_logger, timed_operation

# Remove old logger
# logger = logging.getLogger(__name__)

class ContentPreprocessorService:
    """
    Microservice responsible for content preprocessing and chunking.
    """
    
    def __init__(self):
        self.service_id = "content_preprocessor"
        self.subsystem = SubsystemType.CONTENT
        
        # Enhanced logging with service context
        self.logger = get_content_logger("content_preprocessor")
        
        # Load chunk settings from configuration
        chunk_config = get_chunk_settings()
        self.chunk_size = chunk_config['chunk_size']
        self.chunk_overlap = chunk_config['chunk_overlap']
        
        self.logger.info(f"Initialized Content Preprocessor", 
                        chunk_size=self.chunk_size, 
                        chunk_overlap=self.chunk_overlap)
        
    def __call__(self, state: UniversalState) -> UniversalState:
        """
        Main entry point for content preprocessing.
        Compatible with LangGraph orchestrator.
        """
        operation_id = self.logger.start_operation("content_preprocessing")
        
        try:
            # Extract required inputs from state
            source = state.get("source", "unknown")
            file_path = state.get("file_path", "")
            course_id = state.get("course_id", "default")
            
            self.logger.info(f"Processing content", 
                           source=source, 
                           file_path=file_path, 
                           course_id=course_id)
            
            # Process content based on source type
            if source == "pdf" and file_path:
                result = self.process_pdf_content(file_path)
            elif source == "elasticsearch":
                result = self.process_elasticsearch_content(
                    state.get("es_index", "advanced_docs_elasticsearch_v2")
                )
            elif source == "llm_generated":
                result = self.process_llm_content(
                    state.get("raw_content", "")
                )
            else:
                raise ValueError(f"Unsupported content source: {source}")
            
            # Update state with processed chunks
            chunks_count = len(result.get('chunks', []))
            state.update({
                "chunks": result.get("chunks", []),
                "metadata": result.get("metadata", {}),
                "processing_status": "completed"
            })
            
            self.logger.end_operation(operation_id, success=True, 
                                    chunks_processed=chunks_count,
                                    source_type=source)
            return state
            
        except Exception as e:
            self.logger.end_operation(operation_id, success=False, error=str(e))
            self.logger.log_error_with_context(e, operation="content_preprocessing",
                                             source=state.get("source"),
                                             course_id=state.get("course_id"))
            state.update({
                "processing_status": "failed",
                "error": str(e)
            })
            return state
    
    @timed_operation("pdf_content_processing")
    def process_pdf_content(self, file_path: str) -> Dict[str, Any]:
        """
        Process PDF file and extract chunks.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dict containing processed chunks and metadata
        """
        try:
            from graph.pdf_loader import load_and_chunk_pdf
            
            chunks = load_and_chunk_pdf(file_path)
            
            return {
                "status": "success",
                "content_type": "pdf",
                "chunks": chunks,
                "metadata": {
                    "total_chunks": len(chunks),
                    "chunk_size": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap,
                    "source_file": file_path
                }
            }
        except Exception as e:
            self.logger.error(f"PDF processing failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "content_type": "pdf"
            }
    
    def process_elasticsearch_content(self, es_index: str) -> Dict[str, Any]:
        """
        Process Elasticsearch content and extract existing chunks.
        
        Args:
            es_index: Elasticsearch index name
            
        Returns:
            Dict containing processed chunks and metadata
        """
        try:
            from graph.utils.es_to_kg import load_chunks_from_es
            
            chunks = load_chunks_from_es(es_index)
            
            return {
                "status": "success",
                "content_type": "elasticsearch",
                "chunks": chunks,
                "metadata": {
                    "total_chunks": len(chunks),
                    "source_index": es_index,
                    "pre_chunked": True
                }
            }
        except Exception as e:
            self.logger.error(f"Elasticsearch processing failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "content_type": "elasticsearch"
            }
    
    def process_llm_content(self, raw_content: str) -> Dict[str, Any]:
        """
        Process LLM-generated content and create chunks.
        
        Args:
            raw_content: Raw text content from LLM
            
        Returns:
            Dict containing processed chunks and metadata
        """
        try:
            # Simple chunking for LLM-generated content
            chunks = self._chunk_text(raw_content)
            
            return {
                "status": "success",
                "content_type": "llm_generated",
                "chunks": chunks,
                "metadata": {
                    "total_chunks": len(chunks),
                    "chunk_size": self.chunk_size,
                    "original_length": len(raw_content),
                    "generated": True
                }
            }
        except Exception as e:
            self.logger.error(f"LLM content processing failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "content_type": "llm_generated"
            }
    
    def _chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Chunk text into smaller pieces for processing.
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        text_length = len(text)
        
        for i in range(0, text_length, self.chunk_size - self.chunk_overlap):
            chunk_text = text[i:i + self.chunk_size]
            
            chunks.append({
                "content": chunk_text,
                "metadata": {
                    "chunk_id": len(chunks),
                    "start_char": i,
                    "end_char": min(i + self.chunk_size, text_length)
                }
            })
            
            if i + self.chunk_size >= text_length:
                break
                
        return chunks
    
    def extract_metadata(self, content_type: str, source: str, chunks: List[Dict]) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from processed content.
        
        Args:
            content_type: Type of content processed
            source: Source of the content
            chunks: List of processed chunks
            
        Returns:
            Dict containing extracted metadata
        """
        total_chars = sum(len(chunk.get('content', '')) for chunk in chunks)
        
        metadata = {
            "content_type": content_type,
            "source": source,
            "processing_stats": {
                "total_chunks": len(chunks),
                "total_characters": total_chars,
                "average_chunk_size": total_chars // len(chunks) if chunks else 0,
                "chunk_size_config": self.chunk_size,
                "overlap_config": self.chunk_overlap
            },
            "ready_for_agents": True
        }
        
        return metadata
    
    def preprocess_content(self, content_type: str, **kwargs) -> Dict[str, Any]:
        """
        Main entry point for content preprocessing.
        
        Args:
            content_type: Type of content ('pdf', 'elasticsearch', 'llm_generated')
            **kwargs: Additional arguments specific to content type
            
        Returns:
            Dict containing preprocessing results
        """
        if content_type == "pdf":
            result = self.process_pdf_content(kwargs.get('file_path'))
        elif content_type == "elasticsearch":
            result = self.process_elasticsearch_content(kwargs.get('es_index'))
        elif content_type == "llm_generated":
            result = self.process_llm_content(kwargs.get('raw_content'))
        else:
            return {
                "status": "error",
                "error": f"Unsupported content type: {content_type}"
            }
        
        # Add comprehensive metadata if processing was successful
        if result.get("status") == "success":
            result["comprehensive_metadata"] = self.extract_metadata(
                content_type, 
                kwargs.get('source', 'unknown'),
                result.get("chunks", [])
            )
        
        return result
    
    def get_service_definition(self):
        """Get service definition for registration."""
        from orchestrator.state import ServiceDefinition
        
        return ServiceDefinition(
            service_id=self.service_id,
            subsystem=self.subsystem,
            name="Content Preprocessor",
            description="Handles file upload, chunking, and metadata extraction for various content types",
            dependencies=[],  # No dependencies - entry point
            required_inputs=["source", "file_path", "course_id"],
            provided_outputs=["chunks", "metadata"],
            callable=self,
            timeout_seconds=300  # Reasonable timeout for file processing
        )

def create_content_preprocessor_service():
    """Factory function to create ContentPreprocessorService instance"""
    return ContentPreprocessorService()

# Service instance
content_preprocessor_service = ContentPreprocessorService() 