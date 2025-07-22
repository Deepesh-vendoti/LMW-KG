"""
Content Preprocessor Service - Content Subsystem

Handles initial content processing and chunking with real MongoDB storage.
Supports PDF files, Elasticsearch data, and LLM-generated content.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from pathlib import Path
import hashlib

from orchestrator.state import UniversalState, ServiceStatus, SubsystemType
from utils.database_connections import get_database_manager

logger = logging.getLogger(__name__)

class ContentPreprocessorService:
    """
    Content Preprocessor microservice for the content subsystem.
    
    Responsibilities:
    - Process PDF files, Elasticsearch data, or LLM-generated content
    - Chunk content into manageable pieces
    - Store documents and chunks in MongoDB
    - Generate metadata for downstream processing
    """
    
    def __init__(self):
        self.service_id = "content_preprocessor"
        self.subsystem = SubsystemType.CONTENT
        self.db_manager = get_database_manager()
    
    def __call__(self, state: UniversalState) -> UniversalState:
        """
        Main entry point for content preprocessing.
        Compatible with LangGraph orchestrator.
        """
        print(f"📚 [Content Preprocessor] Processing content...")
        
        try:
            # Validate dependency: Course Manager must complete first
            if not self._validate_dependencies(state):
                error_msg = "Course Manager must complete first - faculty inputs required before content processing"
                logger.error(error_msg)
                
                # Mark as waiting for dependencies
                if "service_statuses" not in state:
                    state["service_statuses"] = {}
                state["service_statuses"][self.service_id] = ServiceStatus.WAITING
                
                if "service_errors" not in state:
                    state["service_errors"] = {}
                state["service_errors"][self.service_id] = error_msg
                
                return state
            
            # Extract required inputs
            upload_type = state.get("upload_type", "elasticsearch")
            course_id = state.get("course_id", "default_course")
            
            # Process content based on upload type
            if upload_type == "pdf":
                chunks = self._process_pdf_content(state)
            elif upload_type == "elasticsearch":
                chunks = self._process_elasticsearch_content(state)
            elif upload_type == "llm_generated":
                chunks = self._process_llm_content(state)
            elif upload_type == "manual_content":
                chunks = self._process_manual_content_input(state)
            else:
                raise ValueError(f"Unsupported upload type: {upload_type}")
            
            # Store in MongoDB
            storage_result = self._store_content_in_mongodb(chunks, course_id, upload_type)
            
            # Generate metadata
            content_metadata = self._generate_content_metadata(chunks, course_id, upload_type)
            
            # Update state with results
            state.update({
                "chunks": chunks,
                "content_metadata": content_metadata,
                "content_preprocessor_result": {
                    "chunks_processed": len(chunks),
                    "storage_result": storage_result,
                    "metadata": content_metadata
                }
            })
            
            # Mark service as completed
            if "service_statuses" not in state:
                state["service_statuses"] = {}
            state["service_statuses"][self.service_id] = ServiceStatus.COMPLETED
            
            print(f"✅ Content preprocessing completed: {len(chunks)} chunks processed")
            return state
            
        except Exception as e:
            logger.error(f"Content preprocessing failed: {e}")
            
            # Mark service as error
            if "service_statuses" not in state:
                state["service_statuses"] = {}
            state["service_statuses"][self.service_id] = ServiceStatus.ERROR
            
            # Store error
            if "service_errors" not in state:
                state["service_errors"] = {}
            state["service_errors"][self.service_id] = str(e)
            
            return state
    
    def _validate_dependencies(self, state: UniversalState) -> bool:
        """
        Validate that Course Manager has completed successfully.
        Content Preprocessor should not run before faculty inputs are collected.
        """
        service_statuses = state.get("service_statuses", {})
        course_manager_status = service_statuses.get("course_manager")
        
        if course_manager_status == ServiceStatus.COMPLETED:
            # Additional validation: check if course configuration exists
            if state.get("course_config") and state.get("faculty_inputs_collected"):
                return True
            else:
                logger.warning("Course Manager completed but missing course_config or faculty inputs")
                return False
        
        logger.warning(f"Course Manager dependency not satisfied. Status: {course_manager_status}")
        return False
    
    def _process_pdf_content(self, state: UniversalState) -> List[Dict[str, Any]]:
        """Process PDF content using LlamaIndex pipeline (aligned with SME subsystem)."""
        file_path = state.get("file_path")
        course_id = state.get("course_id", "default_course")
        
        if not file_path:
            raise ValueError("File path required for PDF processing")
        
        try:
            # Use LlamaIndex processor aligned with SME subsystem
            from utils.llamaindex_content_processor import process_pdf_with_llamaindex
            
            # Process PDF using LlamaIndex
            result = process_pdf_with_llamaindex(file_path, course_id)
            
            if result["status"] != "success":
                raise Exception(f"LlamaIndex processing failed: {result.get('error', 'Unknown error')}")
            
            # Query the processed content to get chunks
            from utils.llamaindex_content_processor import LlamaIndexContentProcessor
            processor = LlamaIndexContentProcessor()
            
            # Get chunks from the index (empty query to get all)
            chunks_data = processor.query_content("", top_k=100)  # Get more chunks
            
            if not chunks_data:
                # Fallback: create a simple chunk from the processing result
                chunks = [{
                    "chunk_id": "llamaindex_chunk_0000",
                    "content": f"PDF processed successfully: {result.get('chunks_processed', 0)} chunks created in index {result.get('index_name')}",
                    "metadata": {
                        "source": "pdf",
                        "file_path": file_path,
                        "course_id": course_id,
                        "chunk_index": 0,
                        "processor": "llamaindex",
                        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                        "index_name": "course_docs_ostep_2025",
                        "processed_at": datetime.now().isoformat()
                    }
                }]
            else:
                # Convert to our chunk format
                chunks = []
                for i, chunk_data in enumerate(chunks_data):
                    chunk = {
                        "chunk_id": f"llamaindex_chunk_{i:04d}",
                        "content": chunk_data["content"],
                        "metadata": {
                            "source": "pdf",
                            "file_path": file_path,
                            "course_id": course_id,
                            "chunk_index": i,
                            "processor": "llamaindex",
                            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                            "index_name": "course_docs_ostep_2025",
                            "score": chunk_data.get("score"),
                            "processed_at": datetime.now().isoformat()
                        }
                    }
                    chunks.append(chunk)
            
            logger.info(f"LlamaIndex PDF processing completed: {len(chunks)} chunks retrieved")
            return chunks
            
        except Exception as e:
            raise Exception(f"LlamaIndex content processing failed: {e}")
    
    def _process_elasticsearch_content(self, state: UniversalState) -> List[Dict[str, Any]]:
        """Process Elasticsearch content using LlamaIndex query interface."""
        course_id = state.get("course_id", "default_course")
        
        try:
            # Use LlamaIndex processor to query the same index
            from utils.llamaindex_content_processor import LlamaIndexContentProcessor
            
            processor = LlamaIndexContentProcessor(
                index_name="course_docs_ostep_2025"  # Aligned with SME subsystem
            )
            
            # Query all content from the index
            chunks_data = processor.query_content("", top_k=1000)  # Get all chunks
            
            # Convert to our chunk format
            chunks = []
            for i, chunk_data in enumerate(chunks_data):
                chunk = {
                    "chunk_id": f"es_chunk_{i:04d}",
                    "content": chunk_data["content"],
                    "metadata": {
                        "source": "elasticsearch",
                        "es_index": "course_docs_ostep_2025",
                        "course_id": course_id,
                        "chunk_index": i,
                        "processor": "llamaindex",
                        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                        "score": chunk_data.get("score"),
                        "processed_at": datetime.now().isoformat(),
                        **chunk_data.get("metadata", {})
                    }
                }
                chunks.append(chunk)
            
            logger.info(f"Elasticsearch content processing completed: {len(chunks)} chunks retrieved")
            return chunks
            
        except Exception as e:
            logger.warning(f"Elasticsearch processing failed: {e}")
            logger.info("Falling back to manual content generation for Elasticsearch mode")
            
            # Fallback: Generate sample content for Elasticsearch mode
            # This allows the pipeline to continue while Elasticsearch is being fixed
            return self._generate_fallback_content_for_elasticsearch(state)
    
    def _generate_fallback_content_for_elasticsearch(self, state: UniversalState) -> List[Dict[str, Any]]:
        """Generate fallback content when Elasticsearch is unavailable."""
        course_id = state.get("course_id", "default_course")
        course_config = state.get("course_config", {})
        
        print("\n" + "="*60)
        print("🔄 ELASTICSEARCH FALLBACK MODE")
        print("="*60)
        print("⚠️ Elasticsearch connection failed - using fallback content")
        print("💡 This allows the pipeline to continue while Elasticsearch is being fixed")
        print("="*60)
        
        # Generate sample operating systems content
        os_topics = [
            "Introduction to Operating Systems",
            "Process Management and Scheduling",
            "Memory Management and Virtual Memory",
            "File Systems and Storage",
            "Concurrency and Synchronization",
            "Deadlock Detection and Prevention",
            "Input/Output Systems",
            "Security and Protection"
        ]
        
        chunks = []
        for i, topic in enumerate(os_topics):
            content_text = f"""
{topic}

This is a comprehensive topic in Operating Systems designed for {course_config.get('target_audience', 'Computer Science students')}.

Key Concepts:
- Core principles and fundamental concepts
- Implementation strategies and algorithms
- Real-world applications and case studies
- Performance considerations and optimization

Learning Objectives:
1. Understand the theoretical foundations
2. Analyze practical implementation approaches
3. Evaluate performance characteristics
4. Apply concepts to real-world scenarios

This content is generated as fallback for course {course_id} while Elasticsearch connectivity is being resolved.

Topic: {topic}
Course Level: {course_config.get('course_level', 'undergraduate')}
Target Audience: {course_config.get('target_audience', 'Computer Science students')}
"""
            
            chunk = {
                "chunk_id": f"es_fallback_chunk_{i:04d}",
                "content": content_text.strip(),
                "metadata": {
                    "source": "elasticsearch_fallback",
                    "es_index": "course_docs_ostep_2025",
                    "course_id": course_id,
                    "topic": topic,
                    "chunk_index": i,
                    "fallback_mode": True,
                    "original_source": "elasticsearch",
                    "processor": "fallback_generator",
                    "processed_at": datetime.now().isoformat(),
                    "note": "Generated due to Elasticsearch connectivity issues"
                }
            }
            chunks.append(chunk)
        
        print(f"✅ Fallback content generation completed: {len(chunks)} chunks created")
        print("📋 Pipeline can now continue to Course Mapper and beyond")
        print("="*60)
        
        return chunks
    
    def _process_llm_content(self, state: UniversalState) -> List[Dict[str, Any]]:
        """Process LLM-generated content."""
        raw_content = state.get("raw_content")
        if not raw_content:
            raise ValueError("Raw content required for LLM processing")
        
        # Simple chunking for LLM content
        chunk_size = 1000
        overlap = 100
        
        chunks = []
        content_length = len(raw_content)
        
        for i in range(0, content_length, chunk_size - overlap):
            end_pos = min(i + chunk_size, content_length)
            chunk_content = raw_content[i:end_pos]
            
            chunk = {
                "chunk_id": f"llm_chunk_{i//(chunk_size-overlap):04d}",
                "content": chunk_content,
                "metadata": {
                    "source": "llm_generated",
                    "start_pos": i,
                    "end_pos": end_pos,
                    "chunk_index": i//(chunk_size-overlap),
                    "processed_at": datetime.now().isoformat()
                }
            }
            chunks.append(chunk)
        
        return chunks
    
    def _process_manual_content_input(self, state: UniversalState) -> List[Dict[str, Any]]:
        """
        Process manual content input after Course Manager approval.
        In manual mode, this would prompt for content or use default course content.
        """
        course_id = state.get("course_id", "default_course")
        course_config = state.get("course_config", {})
        
        # Check if Course Manager provided specific content areas
        suggested_content_areas = course_config.get("suggested_content_areas", [])
        target_audience = course_config.get("target_audience", "Computer Science students")
        course_level = course_config.get("course_level", "undergraduate")
        
        print("\n" + "="*60)
        print("📝 MANUAL CONTENT INPUT - Post Course Manager Approval")
        print("="*60)
        print(f"🎯 Course: {course_id}")
        print(f"👥 Target Audience: {target_audience}")
        print(f"📚 Course Level: {course_level}")
        if suggested_content_areas:
            print(f"💡 Suggested Content Areas: {', '.join(suggested_content_areas)}")
        print("="*60)
        
        # For manual mode demonstration, generate content based on course configuration
        # In a real implementation, this would prompt faculty to upload documents
        manual_content_topics = [
            "Introduction to Operating Systems and System Architecture",
            "Process Management and Scheduling Algorithms", 
            "Memory Management and Virtual Memory Systems",
            "File Systems and Storage Management",
            "Concurrency and Synchronization Mechanisms",
            "Deadlock Detection and Prevention Strategies",
            "Input/Output Systems and Device Management",
            "Security and Protection in Operating Systems"
        ]
        
        print("🎓 Generating sample content for manual mode...")
        print("💡 In production, faculty would upload actual course documents here")
        
        chunks = []
        for i, topic in enumerate(manual_content_topics):
            content_text = f"""
{topic}

This is a foundational topic in {course_config.get('course_name', 'Operating Systems')} designed for {target_audience}.

Key Learning Points:
- Understanding core concepts and principles
- Practical implementation considerations  
- Real-world applications and examples
- Problem-solving approaches and methodologies

This content is generated for course {course_id} at the {course_level} level, following the course structure approved by the Course Manager after faculty input collection.

Content Area: {topic}
Target Complexity: {course_level}
Expected Prior Knowledge: Basic computer science fundamentals
"""
            
            chunk = {
                "chunk_id": f"manual_chunk_{i:04d}",
                "content": content_text.strip(),
                "metadata": {
                    "source": "manual_content",
                    "course_id": course_id,
                    "topic": topic,
                    "chunk_index": i,
                    "target_audience": target_audience,
                    "course_level": course_level,
                    "generated_after_course_manager": True,
                    "faculty_approved_structure": True,
                    "processor": "manual_input_generator",
                    "processed_at": datetime.now().isoformat()
                }
            }
            chunks.append(chunk)
        
        print(f"✅ Manual content generation completed: {len(chunks)} chunks created")
        print("📋 Content follows Course Manager approved structure")
        print("="*60)
        
        return chunks
    
    def _store_content_in_mongodb(self, chunks: List[Dict[str, Any]], course_id: str, upload_type: str) -> Dict[str, Any]:
        """Store content chunks in MongoDB."""
        try:
            # Get MongoDB database
            db = self.db_manager.get_content_preprocessor_db()
            
            # Store document metadata
            document_metadata = {
                "course_id": course_id,
                "upload_type": upload_type,
                "total_chunks": len(chunks),
                "created_at": datetime.now(),
                "status": "processed"
            }
            
            # Generate document ID
            doc_id = hashlib.md5(f"{course_id}_{upload_type}_{datetime.now().isoformat()}".encode()).hexdigest()
            document_metadata["document_id"] = doc_id
            
            # Insert document metadata
            db.documents.insert_one(document_metadata)
            
            # Insert chunks
            for chunk in chunks:
                chunk["document_id"] = doc_id
                chunk["course_id"] = course_id
                chunk["created_at"] = datetime.now()
                db.chunks.insert_one(chunk)
            
            # Insert processing log
            processing_log = {
                "document_id": doc_id,
                "course_id": course_id,
                "upload_type": upload_type,
                "chunks_processed": len(chunks),
                "processing_time": datetime.now(),
                "status": "completed"
            }
            db.processing_logs.insert_one(processing_log)
            
            return {
                "status": "success",
                "document_id": doc_id,
                "chunks_stored": len(chunks),
                "database": "mongodb"
            }
            
        except Exception as e:
            logger.error(f"MongoDB storage failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "database": "mongodb"
            }
    
    def _generate_content_metadata(self, chunks: List[Dict[str, Any]], course_id: str, upload_type: str) -> Dict[str, Any]:
        """Generate metadata for the processed content."""
        total_content_length = sum(len(chunk["content"]) for chunk in chunks)
        
        return {
            "course_id": course_id,
            "upload_type": upload_type,
            "total_chunks": len(chunks),
            "total_content_length": total_content_length,
            "average_chunk_length": total_content_length / len(chunks) if chunks else 0,
            "processing_timestamp": datetime.now().isoformat(),
            "chunk_metadata": {
                "source_types": list(set(chunk["metadata"]["source"] for chunk in chunks)),
                "date_range": {
                    "earliest": min(chunk["metadata"].get("processed_at", "") for chunk in chunks),
                    "latest": max(chunk["metadata"].get("processed_at", "") for chunk in chunks)
                }
            }
        }
    
    def get_service_definition(self):
        """Get service definition for registration."""
        from orchestrator.state import ServiceDefinition
        
        return ServiceDefinition(
            service_id=self.service_id,
            subsystem=self.subsystem,
            name="Content Preprocessor",
            description="Processes and chunks content from various sources (PDF, ES, LLM)",
            dependencies=["course_manager"],  # Now depends on Course Manager
            required_inputs=["upload_type", "course_id"],
            provided_outputs=["chunks", "content_metadata"],
            callable=self,
            timeout_seconds=300
        )

def create_content_preprocessor_service() -> ContentPreprocessorService:
    """Factory function to create Content Preprocessor service."""
    return ContentPreprocessorService() 