# LangGraph Knowledge Graph System

A comprehensive knowledge graph system built with LangGraph and LangChain for personalized learning path generation and course knowledge structuring.

## 🌟 Features

- **Multi-Agent Pipeline**: 7-agent LangGraph pipeline for knowledge extraction and structuring
- **Personalized Learning Trees (PLT)**: Generate personalized learning paths for individual learners
- **Neo4j Integration**: Store and query knowledge graphs with complex relationships
- **Course-Level Knowledge Graphs**: Full course structure with Learning Objectives → Knowledge Components → Instruction Methods → Resources
- **KLI-Aware Processing**: Knowledge Component classification and Learning Process identification

## 🏗️ Architecture

### Stage 1: Knowledge Structuring Pipeline
1. **Researcher Agent** → 2. **LO Generator Agent** → 3. **Curator Agent** → 4. **Analyst Agent** → 5. **KC Classifier Agent**

### Stage 2: Learning Process & Instruction Pipeline
6. **Learning Process Identifier Agent** → 7. **Instruction Agent**

### PLT Generation Pipeline
- Accept Learner Context → Prioritize LOs → Map KCs → Sequence KCs → Match IMs → Link Resources

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
│   └── state.py          # State schemas
├── prompts/              # Agent prompt templates
├── main.py              # CLI runner
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