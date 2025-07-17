# Resource Schema Documentation

## Overview
This document defines the unified resource schema used across the LangGraph Knowledge Graph system.

## Resource Schema Standards

### 1. PLT Resources (Personalized Learning Tree)
Used in `graph/agents_plt.py` for mock resource generation:

```python
{
    "resource_id": "res_123",
    "name": "Resource Name",
    "type": "interactive",  # interactive, video, text, etc.
    "format": "web",        # web, pdf, video, etc.
    "difficulty": "medium"  # easy, medium, hard
}
```

### 2. Course-Level KG Resources
Used in `graph/db.py` for course knowledge graph:

```python
{
    "method": "Instruction Method Description",  # Links to IM
    "url": "https://example.com/resource",
    "title": "Resource Title"
}
```

### 3. Instruction Method Resources
Used in `graph/db.py` for linking resources to instruction methods:

```python
{
    "resource_id": "res_123",
    "name": "Resource Name",
    "type": "interactive",
    "format": "web",
    "difficulty": "medium",
    "url": "https://example.com/resource",
    "title": "Resource Title"
}
```

## Neo4j Node Properties

### LearningObjective
- `id`: Unique identifier (used for relationships)
- `text`: Human-readable description

### KnowledgeComponent
- `id`: Unique identifier (used for relationships)
- `text`: Human-readable description

### LearningProcess
- `id`: Unique identifier (used for relationships)
- `type`: Process type (Understanding, Application, etc.)

### InstructionMethod
- `id`: Unique identifier (used for relationships)
- `description`: Method description
- `type`: Method type (Visualization, Problem Solving, etc.)

### Resource
- `resource_id`: Unique identifier
- `name`: Resource name
- `type`: Resource type
- `format`: Resource format
- `difficulty`: Difficulty level
- `url`: Resource URL
- `title`: Resource title

## Relationships
- `(:Course)-[:HAS_LO]->(:LearningObjective)`
- `(:LearningObjective)-[:HAS_KC]->(:KnowledgeComponent)`
- `(:KnowledgeComponent)-[:DELIVERED_BY]->(:InstructionMethod)`
- `(:InstructionMethod)-[:USES_RESOURCE]->(:Resource)`
- `(:LearningObjective)-[:NEXT]->(:LearningObjective)`
- `(:KnowledgeComponent)-[:REQUIRES]->(:LearningProcess)`
- `(:LearningProcess)-[:BEST_SUPPORTED_BY]->(:InstructionMethod)` 