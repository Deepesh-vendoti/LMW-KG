"""
Content Subsystem

Handles course content processing, knowledge graph generation, and faculty approval workflows.

Services:
- Content Preprocessor: File upload, chunking, metadata extraction
"""

from .services import ContentPreprocessorService

__all__ = [
    "ContentPreprocessorService"
] 