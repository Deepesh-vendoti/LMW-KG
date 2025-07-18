"""
Unified LangGraph Orchestrator

This orchestrates all 8 microservice responsibilities as LangGraph subgraphs:
1. Course Manager -> 2. Content Preprocessor -> 3. Course Content Mapper (Stage 1) 
-> 4. KLI Application (Stage 2) -> 5. Knowledge Graph Generator 
-> 6. Query Strategy Manager -> 7. Graph Query Engine -> 8. Learning Tree Handler

Includes faculty approval checkpoints: FACD, FCCS, FFCS
"""

import json
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage

# Import state schemas
from graph.unified_state import (
    UnifiedState, 
    FACDSchema, 
    FCCSSchema, 
    FFCSSchema
)

# Import existing components
from graph.graph import build_graph_stage_1, build_graph_stage_2
from graph.plt_generator import build_plt_graph
from graph.utils.es_to_kg import transform_es_to_kg, validate_es_connection
from graph.pdf_loader import load_pdf_as_chunks
from graph.db import insert_course_kg_to_neo4j, insert_plt_to_neo4j

# Import new microservices
from services.course_manager import course_manager_service
from services.content_preprocessor import content_preprocessor_service

# ===============================
# SUBGRAPH 1: COURSE MANAGER
# ===============================

def course_manager_subgraph(state: UnifiedState) -> UnifiedState:
    """
    Microservice 1: Course Manager
    Purpose: Assist faculty in bootstrapping course with minimal input
    
    Handles:
    - Upload content (PDFs, docs)
    - Fetch from Elasticsearch 
    - LLM-based fallback generation
    """
    print("📋 [Course Manager] Executing...")
    
    try:
        # Use the new CourseManager service
        result = course_manager_service.process_course_input(
            upload_type=state.get("upload_type", "pdf"),
            file_path=state.get("file_path"),
            course_id=state.get("course_id"),
            es_index=state.get("es_index"),
            topic=state.get("topic", "General Course Content")
        )
        
        # Bridge service result to LangGraph state
        if result.get("status") == "success":
            state["course_manager_result"] = result
            state["current_stage"] = "course_manager"
            state["completed_stages"] = state.get("completed_stages", []) + ["course_manager"]
            
            # Store content for next stage
            if result.get("content"):
                state["raw_content"] = result["content"]
            
            print(f"✅ Course Manager configured for {result.get('upload_type')} processing")
        else:
            state["errors"] = state.get("errors", []) + [f"Course Manager error: {result.get('error')}"]
        
        return state
        
    except Exception as e:
        state["errors"] = state.get("errors", []) + [f"Course Manager error: {str(e)}"]
        return state

# ===============================
# SUBGRAPH 2: CONTENT PREPROCESSOR  
# ===============================

def content_preprocessor_subgraph(state: UnifiedState) -> UnifiedState:
    """
    Microservice 2: Content Preprocessor
    Purpose: Handle ingestion and chunking of raw content
    
    Pipeline: File Upload -> Text Extraction -> Auto-Chunking -> Metadata extraction
    """
    print("📦 [Content Preprocessor] Executing...")
    
    try:
        # Use the new ContentPreprocessor service
        upload_type = state.get("upload_type", "pdf")
        
        result = content_preprocessor_service.preprocess_content(
            content_type=upload_type,
            file_path=state.get("file_path"),
            es_index=state.get("es_index"),
            raw_content=state.get("raw_content"),
            source=f"{upload_type}_source"
        )
        
        # Bridge service result to LangGraph state
        if result.get("status") == "success":
            state["content_preprocessor_result"] = result
            state["chunks"] = result.get("chunks", [])
            state["metadata"] = result.get("metadata", {})
            state["current_stage"] = "content_preprocessor"
            state["completed_stages"] = state.get("completed_stages", []) + ["content_preprocessor"]
            
            print(f"✅ Content Preprocessor: {len(state['chunks'])} chunks processed")
        else:
            state["errors"] = state.get("errors", []) + [f"Content Preprocessor error: {result.get('error')}"]
        
        return state
        
    except Exception as e:
        state["errors"] = state.get("errors", []) + [f"Content Preprocessor error: {str(e)}"]
        return state

# ===============================
# SUBGRAPH 3: STAGE 1 INTEGRATION
# ===============================

def course_content_mapper_subgraph(state: UnifiedState) -> UnifiedState:
    """
    Microservice 3: Course Content Mapper (Stage 1 Agent)
    Purpose: Extract Learning Objectives (LOs) and early Knowledge Components (KCs)
    
    Uses your existing Stage 1 agents: Researcher -> LO Generator -> Curator -> Analyst -> KC Classifier
    Outputs: FACD (Faculty Approved Course Details)
    """
    print("🧠 [Course Content Mapper - Stage 1] Executing...")
    
    try:
        # Get chunks from previous stage
        chunks = state.get("chunks", [])
        if not chunks:
            state["errors"] = state.get("errors", []) + ["No chunks available for Stage 1 processing"]
            return state
            
        # Build your existing Stage 1 pipeline
        stage1_graph = build_graph_stage_1()
        
        # Process chunks through Stage 1 agents
        learning_objectives = []
        draft_kcs = []
        
        # Process first few chunks for demo (you can expand this)
        for i, chunk in enumerate(chunks[:3]):  # Process first 3 chunks
            chunk_content = chunk["content"]
            print(f"🔄 Processing chunk {i+1} through Stage 1 agents...")
            
            # Run through your existing Stage 1 pipeline
            result = stage1_graph.invoke({"messages": [HumanMessage(content=chunk_content)]})
            
            # Extract structured data from agent responses
            # (You'll need to enhance this based on your actual agent outputs)
            for msg in result["messages"]:
                if hasattr(msg, 'content') and isinstance(msg, AIMessage):
                    content = msg.content
                    # Simple parsing - you can make this more sophisticated
                    if "learning objective" in content.lower():
                        learning_objectives.append({
                            "lo_id": f"LO_{len(learning_objectives)+1:03d}",
                            "text": content[:200] + "...",  # Truncate for demo
                            "source_chunk": i
                        })
                    elif "knowledge component" in content.lower():
                        draft_kcs.append({
                            "kc_id": f"KC_{len(draft_kcs)+1:03d}",
                            "text": content[:200] + "...",
                            "source_chunk": i
                        })
        
        # Create FACD (Faculty Approved Course Details)
        facd = {
            "course_id": state.get("course_id"),
            "learning_objectives": learning_objectives,
            "draft_knowledge_components": draft_kcs,
            "processing_metadata": {
                "chunks_processed": len(chunks[:3]),
                "total_los": len(learning_objectives),
                "total_kcs": len(draft_kcs)
            },
            "faculty_notes": "",
            "requires_revision": False  # Faculty can set this to True if needed
        }
        
        # Store in state
        state["facd"] = facd
        state["facd_approved"] = True  # Auto-approve for demo (faculty can manually review)
        state["current_stage"] = "course_content_mapper"
        state["completed_stages"] = state.get("completed_stages", []) + ["course_content_mapper"]
        
        print(f"✅ Stage 1 completed: {len(learning_objectives)} LOs, {len(draft_kcs)} KCs generated")
        print("📋 FACD (Faculty Approved Course Details) created")
        
        return state
        
    except Exception as e:
        state["errors"] = state.get("errors", []) + [f"Course Content Mapper error: {str(e)}"]
        return state

# ===============================
# SUBGRAPH 4: STAGE 2 INTEGRATION
# ===============================

def kli_application_subgraph(state: UnifiedState) -> UnifiedState:
    """
    Microservice 4: KLI Application (Stage 2 Agent)
    Purpose: Apply KLI tagging to each LO/KC from FACD
    
    Uses your existing Stage 2 agents: LP Identifier -> Instruction Agent
    Outputs: FCCS (Faculty Confirmed Course Structure)
    """
    print("🔁 [KLI Application - Stage 2] Executing...")
    
    try:
        # Get FACD from previous stage
        facd = state.get("facd")
        if not facd or not state.get("facd_approved"):
            state["errors"] = state.get("errors", []) + ["FACD not available or not approved"]
            return state
        
        # Build your existing Stage 2 pipeline
        stage2_graph = build_graph_stage_2()
        
        # Process LOs and KCs through Stage 2 for KLI tagging
        finalized_los = []
        finalized_kcs = []
        learning_processes = []
        instruction_methods = []
        
        # Process Learning Objectives
        for lo in facd["learning_objectives"]:
            lo_text = lo["text"]
            print(f"🔄 Applying KLI tags to LO: {lo['lo_id']}")
            
            # Run through Stage 2 pipeline
            result = stage2_graph.invoke({"messages": [HumanMessage(content=f"LO: {lo_text}")]})
            
            # Extract KLI classifications (enhance based on your actual Stage 2 outputs)
            lp_identified = "Understanding & Sense-Making"  # Default, extract from actual agent response
            im_suggested = "Interactive Exercises"  # Default, extract from actual agent response
            
            finalized_los.append({
                **lo,
                "learning_process": lp_identified,
                "instruction_method": im_suggested,
                "kli_applied": True
            })
            
            # Track unique learning processes and instruction methods
            if lp_identified not in [lp["type"] for lp in learning_processes]:
                learning_processes.append({"type": lp_identified, "description": "KLI Framework classification"})
            if im_suggested not in [im["type"] for im in instruction_methods]:
                instruction_methods.append({"type": im_suggested, "description": "Suggested delivery method"})
        
        # Process Knowledge Components 
        for kc in facd["draft_knowledge_components"]:
            kc_text = kc["text"]
            print(f"🔄 Applying KLI tags to KC: {kc['kc_id']}")
            
            # Run through Stage 2 pipeline
            result = stage2_graph.invoke({"messages": [HumanMessage(content=f"KC: {kc_text}")]})
            
            # Extract KLI classifications
            lp_identified = "Memory & Fluency"  # Default, extract from actual agent response
            im_suggested = "Flashcards"  # Default, extract from actual agent response
            
            finalized_kcs.append({
                **kc,
                "learning_process": lp_identified,
                "instruction_method": im_suggested,
                "kli_applied": True
            })
        
        # Create FCCS (Faculty Confirmed Course Structure)
        fccs = {
            "course_id": state.get("course_id"),
            "finalized_los": finalized_los,
            "finalized_kcs": finalized_kcs,
            "learning_processes": learning_processes,
            "instruction_methods": instruction_methods,
            "kli_metadata": {
                "total_los_processed": len(finalized_los),
                "total_kcs_processed": len(finalized_kcs),
                "unique_learning_processes": len(learning_processes),
                "unique_instruction_methods": len(instruction_methods)
            },
            "faculty_notes": "",
            "requires_revision": False
        }
        
        # Store in state
        state["fccs"] = fccs
        state["fccs_approved"] = True  # Auto-approve for demo
        state["current_stage"] = "kli_application"
        state["completed_stages"] = state.get("completed_stages", []) + ["kli_application"]
        
        print(f"✅ Stage 2 completed: KLI tags applied to {len(finalized_los)} LOs and {len(finalized_kcs)} KCs")
        print("📋 FCCS (Faculty Confirmed Course Structure) created")
        
        return state
        
    except Exception as e:
        state["errors"] = state.get("errors", []) + [f"KLI Application error: {str(e)}"]
        return state

# ===============================
# SUBGRAPH 5: KNOWLEDGE GRAPH GENERATOR
# ===============================

def knowledge_graph_generator_subgraph(state: UnifiedState) -> UnifiedState:
    """
    Microservice 5: Knowledge Graph Generator
    Purpose: Convert FCCS into Neo4j-based KG + MongoDB snapshot + PostgreSQL view
    
    Outputs: FFCS (Faculty Finalized Course Structure)
    """
    print("🧩 [Knowledge Graph Generator] Executing...")
    
    try:
        # Get FCCS from previous stage
        fccs = state.get("fccs")
        if not fccs or not state.get("fccs_approved"):
            state["errors"] = state.get("errors", []) + ["FCCS not available or not approved"]
            return state
        
        # Convert FCCS to your existing course graph format
        course_graph = {
            "course_id": state.get("course_id"),
            "title": f"Course {state.get('course_id')} (Orchestrated)",
            "learning_objectives": []
        }
        
        # Transform FCCS to course graph format
        for lo in fccs["finalized_los"]:
            lo_entry = {
                "lo_id": lo["lo_id"],
                "text": lo["text"],
                "kcs": []
            }
            
            # Find related KCs for this LO
            for kc in fccs["finalized_kcs"]:
                if kc.get("source_chunk") == lo.get("source_chunk"):  # Simple relationship logic
                    kc_entry = {
                        "kc_id": kc["kc_id"],
                        "text": kc["text"],
                        "learning_process": kc["learning_process"],
                        "instruction_methods": [kc["instruction_method"]]
                    }
                    lo_entry["kcs"].append(kc_entry)
            
            course_graph["learning_objectives"].append(lo_entry)
        
        # Insert into Neo4j using your existing function
        print("🔄 Inserting knowledge graph into Neo4j...")
        insert_course_kg_to_neo4j(course_graph, clear_existing=True)
        
        # Create FFCS (Faculty Finalized Course Structure)
        ffcs = {
            "course_id": state.get("course_id"),
            "final_structure": course_graph,
            "neo4j_ready": True,
            "faculty_final_approval": True,
            "storage_locations": {
                "neo4j": "bolt://localhost:7687",
                "mongodb_snapshot": "placeholder_collection",  # You can implement this
                "postgresql_ffcs": "placeholder_table"  # You can implement this
            },
            "approval_timestamp": "2025-01-27T12:00:00Z"
        }
        
        # Store in state
        state["ffcs"] = ffcs
        state["ffcs_approved"] = True
        state["neo4j_graph"] = course_graph
        state["current_stage"] = "knowledge_graph_generator"
        state["completed_stages"] = state.get("completed_stages", []) + ["knowledge_graph_generator"]
        
        print("✅ Knowledge Graph Generator completed")
        print("📋 FFCS (Faculty Finalized Course Structure) created")
        print(f"📊 Neo4j nodes: {len(course_graph['learning_objectives'])} LOs")
        
        return state
        
    except Exception as e:
        state["errors"] = state.get("errors", []) + [f"Knowledge Graph Generator error: {str(e)}"]
        return state

# ===============================
# SUBGRAPH 6-8: LEARNER-FOCUSED SUBGRAPHS
# ===============================

def query_strategy_manager_subgraph(state: UnifiedState) -> UnifiedState:
    """
    Microservice 6: Query Strategy Manager
    Purpose: Bridge Learner Subsystem -> Graph Actions
    """
    print("🧠 [Query Strategy Manager] Executing...")
    
    try:
        learner_id = state.get("learner_id")
        if not learner_id:
            # Skip if no learner context provided
            print("⏭️  No learner context provided, skipping learner-focused stages")
            state["next_action"] = "complete"
            return state
        
        # Simple strategy decision logic (you can enhance this)
        learner_context = state.get("learner_context", {})
        decision_label = learner_context.get("decision_label", "Standard Learner")
        
        if "struggling" in decision_label.lower():
            strategy = "plt_generation"
        elif "advanced" in decision_label.lower():
            strategy = "subgraph"
        else:
            strategy = "recommendation"
        
        state["query_strategy"] = strategy
        state["current_stage"] = "query_strategy_manager"
        state["completed_stages"] = state.get("completed_stages", []) + ["query_strategy_manager"]
        
        print(f"✅ Query Strategy: {strategy} for learner {learner_id}")
        return state
        
    except Exception as e:
        state["errors"] = state.get("errors", []) + [f"Query Strategy Manager error: {str(e)}"]
        return state

def graph_query_engine_subgraph(state: UnifiedState) -> UnifiedState:
    """
    Microservice 7: Graph Query Engine  
    Purpose: Generate & run Cypher queries on Neo4j
    """
    print("🔍 [Graph Query Engine] Executing...")
    
    try:
        strategy = state.get("query_strategy")
        if not strategy:
            print("⏭️  No query strategy defined, skipping graph queries")
            return state
        
        # Generate appropriate Cypher queries based on strategy
        cypher_queries = []
        
        if strategy == "plt_generation":
            cypher_queries = [
                "MATCH (c:Course)-[:HAS_LO]->(lo:LearningObjective) RETURN c, lo LIMIT 10",
                "MATCH (lo:LearningObjective)-[:HAS_KC]->(kc:KnowledgeComponent) RETURN lo, kc LIMIT 20"
            ]
        elif strategy == "subgraph":
            cypher_queries = [
                "MATCH (lo:LearningObjective)-[:HAS_KC]->(kc:KnowledgeComponent) RETURN lo, kc",
            ]
        else:  # recommendation
            cypher_queries = [
                "MATCH (kc:KnowledgeComponent)-[:DELIVERED_BY]->(im:InstructionMethod) RETURN kc, im LIMIT 5"
            ]
        
        # Store query results (placeholder - you'd actually execute these)
        query_results = [{"placeholder": "query_result"} for _ in cypher_queries]
        
        state["cypher_queries"] = cypher_queries
        state["query_results"] = query_results
        state["current_stage"] = "graph_query_engine"
        state["completed_stages"] = state.get("completed_stages", []) + ["graph_query_engine"]
        
        print(f"✅ Graph Query Engine: {len(cypher_queries)} queries prepared")
        return state
        
    except Exception as e:
        state["errors"] = state.get("errors", []) + [f"Graph Query Engine error: {str(e)}"]
        return state

def learning_tree_handler_subgraph(state: UnifiedState) -> UnifiedState:
    """
    Microservice 8: Learning Tree Handler
    Purpose: Maintain learner-specific Personalized Learning Trees (PLTs)
    
    Uses your existing PLT generator
    """
    print("🌳 [Learning Tree Handler] Executing...")
    
    try:
        strategy = state.get("query_strategy")
        if strategy != "plt_generation":
            print("⏭️  PLT generation not requested, skipping Learning Tree Handler")
            state["next_action"] = "complete"
            return state
        
        learner_id = state.get("learner_id")
        course_id = state.get("course_id")
        
        if not learner_id or not course_id:
            state["errors"] = state.get("errors", []) + ["Missing learner_id or course_id for PLT generation"]
            return state
        
        # Use your existing PLT generator
        from graph.plt_generator import run_plt_generator
        
        print(f"🔄 Generating PLT for learner {learner_id} in course {course_id}")
        plt_result = run_plt_generator(learner_id=learner_id, course_id=course_id)
        
        if plt_result and "final_plt" in plt_result:
            plt_data = plt_result["final_plt"]
            
            # Insert into Neo4j using your existing function
            insert_plt_to_neo4j(plt_data, clear_existing=True)
            
            state["plt_data"] = plt_data
            state["redis_plt"] = f"plt:{learner_id}:{course_id}"  # Redis key placeholder
            state["postgresql_plt_version"] = 1  # Version placeholder
            
            print(f"✅ PLT generated: {len(plt_data.get('learning_path', []))} learning steps")
        else:
            state["errors"] = state.get("errors", []) + ["PLT generation failed"]
            return state
        
        state["current_stage"] = "learning_tree_handler"
        state["completed_stages"] = state.get("completed_stages", []) + ["learning_tree_handler"]
        state["next_action"] = "complete"
        
        return state
        
    except Exception as e:
        state["errors"] = state.get("errors", []) + [f"Learning Tree Handler error: {str(e)}"]
        return state

# ===============================
# UNIFIED ORCHESTRATOR BUILDER
# ===============================

def build_unified_orchestrator():
    """
    Build the unified LangGraph orchestrator that coordinates all 8 microservice subgraphs
    
    Flow:
    Course Manager -> Content Preprocessor -> Course Content Mapper (Stage 1) 
    -> KLI Application (Stage 2) -> Knowledge Graph Generator 
    -> Query Strategy Manager -> Graph Query Engine -> Learning Tree Handler
    """
    
    orchestrator = StateGraph(UnifiedState)
    
    # Add all subgraph nodes
    orchestrator.add_node("course_manager", course_manager_subgraph)
    orchestrator.add_node("content_preprocessor", content_preprocessor_subgraph)
    orchestrator.add_node("course_content_mapper", course_content_mapper_subgraph)
    orchestrator.add_node("kli_application", kli_application_subgraph)
    orchestrator.add_node("knowledge_graph_generator", knowledge_graph_generator_subgraph)
    orchestrator.add_node("query_strategy_manager", query_strategy_manager_subgraph)
    orchestrator.add_node("graph_query_engine", graph_query_engine_subgraph)
    orchestrator.add_node("learning_tree_handler", learning_tree_handler_subgraph)
    
    # Define the pipeline flow
    orchestrator.set_entry_point("course_manager")
    orchestrator.add_edge("course_manager", "content_preprocessor")
    orchestrator.add_edge("content_preprocessor", "course_content_mapper")
    orchestrator.add_edge("course_content_mapper", "kli_application")
    orchestrator.add_edge("kli_application", "knowledge_graph_generator")
    orchestrator.add_edge("knowledge_graph_generator", "query_strategy_manager")
    orchestrator.add_edge("query_strategy_manager", "graph_query_engine")
    orchestrator.add_edge("graph_query_engine", "learning_tree_handler")
    orchestrator.add_edge("learning_tree_handler", END)
    
    return orchestrator.compile()

# ===============================
# CONVENIENCE FUNCTIONS
# ===============================

def run_course_pipeline(course_id: str, upload_type: str = "pdf", file_path: str = None, 
                       es_index: str = None, learner_id: str = None, learner_context: Dict = None,
                       raw_content: str = None):
    """
    Run the complete course processing pipeline
    
    Args:
        course_id: Course identifier
        upload_type: "pdf", "elasticsearch", or "llm_generated"
        file_path: Path to PDF file (if upload_type="pdf")
        es_index: Elasticsearch index name (if upload_type="elasticsearch")
        raw_content: Raw text content (if upload_type="llm_generated")
        learner_id: Optional learner ID for PLT generation
        learner_context: Optional learner context for personalization
    """
    
    # Build orchestrator
    orchestrator = build_unified_orchestrator()
    
    # Prepare initial state
    initial_state = {
        "course_id": course_id,
        "upload_type": upload_type,
        "session_id": f"session_{course_id}_{upload_type}",
        "errors": [],
        "completed_stages": [],
        "current_stage": "initializing"
    }
    
    if file_path:
        initial_state["file_path"] = file_path
    if es_index:
        initial_state["es_index"] = es_index
    if raw_content:
        initial_state["raw_content"] = raw_content
    if learner_id:
        initial_state["learner_id"] = learner_id
    if learner_context:
        initial_state["learner_context"] = learner_context
    
    print("🚀 Starting Unified LangGraph Orchestrator")
    print("=" * 60)
    print(f"📚 Course: {course_id}")
    print(f"📁 Upload Type: {upload_type}")
    if learner_id:
        print(f"👤 Learner: {learner_id}")
    print("=" * 60)
    
    # Execute the pipeline
    try:
        final_state = orchestrator.invoke(initial_state)
        
        print("\n" + "=" * 60)
        print("🎉 PIPELINE EXECUTION COMPLETED")
        print("=" * 60)
        
        # Print summary
        completed_stages = final_state.get("completed_stages", [])
        errors = final_state.get("errors", [])
        
        print(f"✅ Completed Stages: {len(completed_stages)}")
        for stage in completed_stages:
            print(f"   • {stage}")
        
        if errors:
            print(f"❌ Errors: {len(errors)}")
            for error in errors:
                print(f"   • {error}")
        
        # Print key outputs
        if final_state.get("facd"):
            print(f"\n📋 FACD: {len(final_state['facd']['learning_objectives'])} Learning Objectives")
        if final_state.get("fccs"):
            print(f"📋 FCCS: {len(final_state['fccs']['finalized_los'])} Finalized LOs")
        if final_state.get("ffcs"):
            print(f"📋 FFCS: Knowledge Graph Inserted to Neo4j")
        if final_state.get("plt_data"):
            print(f"🌳 PLT: {len(final_state['plt_data']['learning_path'])} Learning Steps")
        
        return final_state
        
    except Exception as e:
        print(f"❌ Pipeline execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Example usage
    result = run_course_pipeline(
        course_id="OSN",
        upload_type="elasticsearch",
        es_index="advanced_docs_elasticsearch_v2",
        learner_id="R000",
        learner_context={"decision_label": "Standard Learner"}
    ) 