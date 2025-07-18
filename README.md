# LangGraph Knowledge Graph System

A comprehensive knowledge graph system built with LangGraph and LangChain for personalized learning path generation and course knowledge structuring.

## 🌟 Features

- **Multi-Agent Pipeline**: 7-agent LangGraph pipeline for knowledge extraction and structuring
- **Personalized Learning Trees (PLT)**: Generate personalized learning paths for individual learners
- **Neo4j Integration**: Store and query knowledge graphs with complex relationships
- **Course-Level Knowledge Graphs**: Full course structure with Learning Objectives → Knowledge Components → Instruction Methods → Resources
- **KLI-Aware Processing**: Knowledge Component classification and Learning Process identification
- **Elasticsearch Integration**: Transform existing ES chunks into knowledge graphs without re-chunking
- **End-to-End Pipeline**: ES chunks → KG transformation → Neo4j insertion → PLT generation

## 🏗️ Architecture

### Stage 1: Knowledge Structuring Pipeline
1. **Researcher Agent** → 2. **LO Generator Agent** → 3. **Curator Agent** → 4. **Analyst Agent** → 5. **KC Classifier Agent**

### Stage 2: Learning Process & Instruction Pipeline
6. **Learning Process Identifier Agent** → 7. **Instruction Agent**

### PLT Generation Pipeline
- Accept Learner Context → Prioritize LOs → Map KCs → Sequence KCs → Match IMs → Link Resources

### ES to KG Pipeline
- Load ES Chunks → Transform to KG Format → Insert into Neo4j → Generate PLT (optional)

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd langgraph-kg
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup Neo4j**
   - Install Neo4j Desktop or Neo4j Community Edition
   - Start Neo4j server on `bolt://localhost:7687`
   - No authentication required (configured for local development)

## 🚀 Usage

### Run Knowledge Structuring Pipeline
```bash
python main.py stage1
```

### Run Learning Process & Instruction Pipeline
```bash
python main.py stage2
```

### Generate Personalized Learning Tree
```bash
python main.py plt
```

### Elasticsearch to KG to PLT Pipeline
```bash
# Interactive mode
python main.py es

# Command-line mode with options
python generate_kg_from_es.py --course_id OSN --learner_id R000 --generate_plt

# Validate ES connection only
python generate_kg_from_es.py --validate_only
```

### Test PLT Generation
```bash
python test_plt_clean.py
```

## 📊 Knowledge Graph Schema

### Nodes
- `(:Course {id, name})`
- `(:LearningObjective {id, text})`
- `(:KnowledgeComponent {id, text})`
- `(:LearningProcess {id, type})`
- `(:InstructionMethod {id, description, type})`
- `(:Resource {resource_id, name, type, format, difficulty, url, title})`
- `(:PersonalizedLearningStep {learner_id, course_id, lo, kc, priority, sequence, instruction_method})`

### Relationships
- `(:Course)-[:HAS_LO]->(:LearningObjective)`
- `(:LearningObjective)-[:HAS_KC]->(:KnowledgeComponent)`
- `(:KnowledgeComponent)-[:DELIVERED_BY]->(:InstructionMethod)`
- `(:InstructionMethod)-[:USES_RESOURCE]->(:Resource)`
- `(:KnowledgeComponent)-[:REQUIRES]->(:LearningProcess)`
- `(:LearningProcess)-[:BEST_SUPPORTED_BY]->(:InstructionMethod)`

## 🧪 Testing

### Core Functionality Tests
- `test_plt_clean.py`: PLT generation and Neo4j insertion
- `test_generate_plt.py`: PLT generation workflow
- `test_insert_os_data.py`: Knowledge graph insertion
- `test_es_integration.py`: ES integration functionality

### Database Functions
- `insert_plt_to_neo4j()`: Insert personalized learning trees
- `insert_course_kg_to_neo4j()`: Insert course-level knowledge graphs
- `get_plt_for_learner()`: Query personalized learning data
- `get_kcs_under_lo()`: Query knowledge components under learning objectives

## 📁 Project Structure

```
langgraph-kg/
├── graph/
│   ├── agents.py          # Main LangGraph agents
│   ├── agents_plt.py      # PLT-specific agents
│   ├── db.py             # Neo4j database functions
│   ├── graph.py          # LangGraph pipeline definitions
│   ├── plt_generator.py  # PLT generation pipeline
│   ├── utils/
│   │   └── es_to_kg.py   # ES to KG transformation
│   └── state.py          # State schemas
├── prompts/              # Agent prompt templates
├── main.py              # CLI runner
├── generate_kg_from_es.py # ES to KG pipeline script
├── test_es_integration.py # ES integration tests
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## 🔧 Configuration

### Neo4j Connection
- **URI**: `bolt://localhost:7687`
- **Authentication**: None (local development)
- **Database**: Default

### LLM Configuration
- **Model**: Ollama Qwen3:4b
- **Endpoint**: Local Ollama instance

### Elasticsearch Configuration
- **Endpoint**: `http://localhost:9200`
- **Index**: `advanced_docs_elasticsearch_v2`
- **Vector Store Directory**: `./elasticsearch_storage_v2`

## 📈 Example Output

### PLT Generation
```
🌳 Generating Personalized Learning Tree (PLT) for Learner R000...
✅ Generated PLT with 15 steps
✅ Inserted PLT for learner R000 in course OSN with 15 learning steps
```

### Knowledge Graph Query
```
📊 Course → LO → KC relationships: 4
🧠 KC → IM relationships: 4
📖 IM → Resource relationships: 4
```

### ES to KG Pipeline
```
🚀 ES to KG to PLT Pipeline
==================================================
1️⃣ Validating Elasticsearch connection...
✅ Elasticsearch connection and index 'advanced_docs_elasticsearch_v2' validated
📊 Found 150 chunks in Elasticsearch index 'advanced_docs_elasticsearch_v2'

2️⃣ Transforming ES chunks to KG format...
🔄 Loading ES chunks from http://localhost:9200/advanced_docs_elasticsearch_v2
📚 Found 150 chunks in Elasticsearch
✅ Transformed 150 chunks into 25 learning objectives
📊 Total knowledge components: 150

3️⃣ Inserting KG into Neo4j...
✅ Knowledge Graph successfully inserted into Neo4j

4️⃣ Generating Personalized Learning Tree for R000...
✅ Personalized Learning Tree generated successfully!
📊 Generated 15 learning steps

🎉 Pipeline completed successfully!
📚 Course: OSN
📊 Learning Objectives: 25
🧠 Knowledge Components: 150
👤 PLT generated for learner: R000
```

## 🔄 Elasticsearch Integration Workflow

### Prerequisites
1. **Elasticsearch Running**: Ensure ES is accessible at `http://localhost:9200`
2. **Index Exists**: Your ES index should contain chunked documents
3. **Vector Store Data**: LlamaIndex vector store directory should be present

### Workflow Steps
1. **Validation**: Check ES connection and chunk count
2. **Transformation**: Convert ES chunks to internal KG format
3. **Insertion**: Load full KG into Neo4j
4. **PLT Generation**: Create personalized learning trees (optional)

### Configuration Options
- **Course ID**: Customize course identifier (default: "OSN")
- **Learner ID**: Specify target learner for PLT (default: "R000")
- **ES Settings**: Configure endpoint, index, and vector store directory
- **Clear Existing**: Option to clear existing KG data before insertion

### Error Handling
- Graceful handling of ES connection failures
- Validation of chunk count before processing
- Fallback to empty structure if transformation fails
- Detailed error messages for troubleshooting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- LangGraph for the multi-agent orchestration framework
- LangChain for the LLM integration capabilities
- Neo4j for the graph database technology
- Ollama for the local LLM hosting 