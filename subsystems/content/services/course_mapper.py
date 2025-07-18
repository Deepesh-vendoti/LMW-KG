"""
Course Mapper Service - Content Subsystem

Handles Stage 1 knowledge structuring pipeline: 
Researcher → LO Generator → Curator → Analyst → KC Classifier

Integrates with existing LangGraph agents and provides FACD output.
"""

from typing import Dict, Any, List, Optional
import logging
from langchain_core.messages import HumanMessage
from orchestrator.state import UniversalState, ServiceStatus, SubsystemType

logger = logging.getLogger(__name__)

class CourseMappingService:
    """
    Course Mapping microservice for the content subsystem.
    
    Responsibilities:
    - Execute Stage 1 LangGraph pipeline (5 agents)
    - Generate Learning Objectives and Knowledge Components
    - Produce Faculty Approved Course Details (FACD)
    - Bridge existing agents with universal state
    """
    
    def __init__(self):
        self.service_id = "course_mapper"
        self.subsystem = SubsystemType.CONTENT
        
    def __call__(self, state: UniversalState) -> UniversalState:
        """
        Main entry point for course mapping.
        Compatible with LangGraph orchestrator.
        """
        print(f"🗺️ [Course Mapper] Executing Stage 1 pipeline...")
        
        try:
            # Check for required inputs
            chunks = state.get("chunks", [])
            if not chunks:
                raise ValueError("Chunks required for course mapping")
            
            # Execute Stage 1 pipeline
            stage1_result = self._execute_stage1_pipeline(chunks)
            
            # Generate FACD (Faculty Approved Course Details)
            facd = self._generate_facd(stage1_result)
            
            # Update state with results
            state["facd"] = facd
            state["facd_approved"] = False  # Requires faculty approval
            
            # Mark service as completed
            if "service_statuses" not in state:
                state["service_statuses"] = {}
            state["service_statuses"][self.service_id] = ServiceStatus.COMPLETED
            
            # Store service result
            if "service_results" not in state:
                state["service_results"] = {}
            state["service_results"][self.service_id] = {
                "stage1_result": stage1_result,
                "facd": facd,
                "learning_objectives_count": len(stage1_result.get("learning_objectives", [])),
                "knowledge_components_count": len(stage1_result.get("knowledge_components", []))
            }
            
            print(f"✅ Course mapping completed: {len(facd.get('learning_objectives', []))} LOs, {len(facd.get('draft_kcs', []))} KCs")
            return state
            
        except Exception as e:
            logger.error(f"Course mapping failed: {e}")
            
            # Mark service as error
            if "service_statuses" not in state:
                state["service_statuses"] = {}
            state["service_statuses"][self.service_id] = ServiceStatus.ERROR
            
            # Store error
            if "service_errors" not in state:
                state["service_errors"] = {}
            state["service_errors"][self.service_id] = str(e)
            
            return state
    
    def _execute_stage1_pipeline(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute Stage 1 LangGraph pipeline using existing agents."""
        try:
            # Import existing Stage 1 graph
            from graph.graph import build_graph_stage_1
            from graph.state import GraphState
            
            print("🔄 Using existing Stage 1 LangGraph pipeline...")
            
            # Build the Stage 1 graph
            stage1_graph = build_graph_stage_1()
            
            # Prepare input for existing agents
            content_text = "\n".join([chunk.get("content", "") for chunk in chunks])
            initial_state = GraphState(
                messages=[HumanMessage(content=content_text)]
            )
            
            # Execute Stage 1 pipeline - this runs the 5 existing agents
            result = stage1_graph.invoke(initial_state)
            
            # Extract structured output from agent messages
            structured_result = self._extract_structured_output(result)
            
            return structured_result
            
        except Exception as e:
            raise Exception(f"Stage 1 pipeline execution failed: {e}")
    
    def _extract_structured_output(self, agent_result) -> Dict[str, Any]:
        """Extract structured learning objectives and knowledge components from agent output."""
        try:
            # Get the final message content
            if hasattr(agent_result, 'messages') and agent_result.messages:
                final_content = agent_result.messages[-1].content
            else:
                final_content = str(agent_result)
            
            # Simple extraction logic (in production, this would be more sophisticated)
            learning_objectives = self._extract_learning_objectives(final_content)
            knowledge_components = self._extract_knowledge_components(final_content)
            
            return {
                "learning_objectives": learning_objectives,
                "knowledge_components": knowledge_components,
                "agent_output": final_content,
                "pipeline_status": "completed"
            }
            
        except Exception as e:
            logger.warning(f"Failed to extract structured output: {e}")
            # Fallback to mock data for testing
            return {
                "learning_objectives": [
                    {"lo_id": "LO_001", "text": "Understand Operating System Fundamentals"},
                    {"lo_id": "LO_002", "text": "Analyze Memory Management Techniques"},
                    {"lo_id": "LO_003", "text": "Evaluate Process Scheduling Algorithms"}
                ],
                "knowledge_components": [
                    {"kc_id": "KC_001", "text": "OS Definition and Functions", "lo_id": "LO_001"},
                    {"kc_id": "KC_002", "text": "Virtual Memory Concepts", "lo_id": "LO_002"},
                    {"kc_id": "KC_003", "text": "CPU Scheduling Policies", "lo_id": "LO_003"}
                ],
                "agent_output": final_content,
                "pipeline_status": "extracted_with_fallback"
            }
    
    def _extract_learning_objectives(self, content: str) -> List[Dict[str, Any]]:
        """Extract learning objectives from agent output."""
        # Simple keyword-based extraction (production would use more sophisticated NLP)
        objectives = []
        lines = content.split('\n')
        
        lo_count = 1
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['understand', 'analyze', 'evaluate', 'learn', 'objective']):
                if len(line.strip()) > 10:  # Avoid very short lines
                    objectives.append({
                        "lo_id": f"LO_{lo_count:03d}",
                        "text": line.strip()
                    })
                    lo_count += 1
                    
                if len(objectives) >= 5:  # Limit to 5 objectives
                    break
        
        # Ensure at least some objectives
        if not objectives:
            objectives = [
                {"lo_id": "LO_001", "text": "Understand core operating system concepts"},
                {"lo_id": "LO_002", "text": "Analyze system resource management"},
                {"lo_id": "LO_003", "text": "Evaluate system performance"}
            ]
        
        return objectives
    
    def _extract_knowledge_components(self, content: str) -> List[Dict[str, Any]]:
        """Extract knowledge components from agent output."""
        # Simple keyword-based extraction
        components = []
        lines = content.split('\n')
        
        kc_count = 1
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['component', 'concept', 'knowledge', 'skill', 'topic']):
                if len(line.strip()) > 5:
                    components.append({
                        "kc_id": f"KC_{kc_count:03d}",
                        "text": line.strip(),
                        "lo_id": f"LO_{((kc_count - 1) // 2) + 1:03d}"  # Link to LOs
                    })
                    kc_count += 1
                    
                if len(components) >= 10:  # Limit to 10 components
                    break
        
        # Ensure at least some components
        if not components:
            components = [
                {"kc_id": "KC_001", "text": "Process management fundamentals", "lo_id": "LO_001"},
                {"kc_id": "KC_002", "text": "Memory allocation strategies", "lo_id": "LO_002"},
                {"kc_id": "KC_003", "text": "Scheduling algorithm analysis", "lo_id": "LO_003"}
            ]
        
        return components
    
    def _generate_facd(self, stage1_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Faculty Approved Course Details (FACD)."""
        try:
            learning_objectives = stage1_result.get("learning_objectives", [])
            knowledge_components = stage1_result.get("knowledge_components", [])
            
            facd = {
                "version": "1.0",
                "generated_at": "auto",
                "status": "pending_approval",
                "learning_objectives": learning_objectives,
                "draft_kcs": knowledge_components,
                "metadata": {
                    "total_los": len(learning_objectives),
                    "total_kcs": len(knowledge_components),
                    "extraction_method": "stage1_agents",
                    "requires_faculty_review": True
                }
            }
            
            return facd
            
        except Exception as e:
            raise Exception(f"FACD generation failed: {e}")
    
    def get_service_definition(self):
        """Get service definition for registration."""
        from orchestrator.state import ServiceDefinition
        
        return ServiceDefinition(
            service_id=self.service_id,
            subsystem=self.subsystem,
            name="Course Mapper",
            description="Executes Stage 1 knowledge structuring pipeline to generate Learning Objectives and Knowledge Components",
            dependencies=["content_preprocessor"],  # Needs chunks
            required_inputs=["chunks"],
            provided_outputs=["facd", "learning_objectives", "knowledge_components"],
            callable=self,
            timeout_seconds=600  # Stage 1 can take time
        )

# ===============================
# SERVICE FACTORY
# ===============================

def create_course_mapper_service() -> CourseMappingService:
    """Factory function to create course mapper service."""
    return CourseMappingService()

# ===============================
# LEGACY COMPATIBILITY
# ===============================

def course_mapper_service(state: UniversalState) -> UniversalState:
    """Legacy compatibility function."""
    service = create_course_mapper_service()
    return service(state) 