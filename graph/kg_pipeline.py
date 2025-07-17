import json
import sys
import os
import re

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import directly from the files
from langchain_core.messages import HumanMessage, AIMessage
from langchain_ollama import OllamaLLM
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel
from typing import List
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END

# Define the state schema
class GraphState(BaseModel):
    messages: List[BaseMessage]

# KLI-Aware Knowledge Graph Schema
class KGNodeTypes:
    KC = "KnowledgeComponent"
    FACT = "Fact"
    EXAMPLE = "Example"
    CONCEPT = "Concept"
    PROCEDURE = "Procedure"
    STRATEGY = "Strategy"

class KGRelationships:
    SUPPORTS = "SUPPORTS"
    HAS_TYPE = "HAS_TYPE"
    REQUIRES_PROCESS = "REQUIRES_PROCESS"
    EXPLAINS = "EXPLAINS"
    IS_PART_OF = "IS_PART_OF"

def parse_kc_classification(response_text):
    """Parse KC classification from agent response"""
    try:
        # Try to extract JSON from the response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            parsed = json.loads(json_str)
            return {
                "kc_type": parsed.get("kc_type", "Conceptual"),
                "learning_process": parsed.get("learning_process", "Understanding"),
                "reasoning": parsed.get("reasoning", "No reasoning provided")
            }
    except (json.JSONDecodeError, AttributeError):
        pass
    
    # Fallback: try to extract from text
    kc_type = "Conceptual"  # default
    learning_process = "Understanding"  # default
    
    if any(word in response_text.lower() for word in ["fact", "definition", "date", "name"]):
        kc_type = "Factual"
        learning_process = "Memory"
    elif any(word in response_text.lower() for word in ["procedure", "step", "how to", "process"]):
        kc_type = "Procedural"
        learning_process = "Induction"
    elif any(word in response_text.lower() for word in ["strategy", "when", "why", "decision"]):
        kc_type = "Strategic"
        learning_process = "Strategic"
    
    return {
        "kc_type": kc_type,
        "learning_process": learning_process,
        "reasoning": "Fallback classification based on keyword matching"
    }

# Agent functions
def create_researcher_agent():
    llm = OllamaLLM(model="qwen3:4b")
    
    def researcher(state: GraphState) -> GraphState:
        if state.messages:
            last_message = state.messages[-1]
            query = last_message.content
            response = llm.invoke(query)
            state.messages.append(AIMessage(content=response))
        return state
    
    return RunnableLambda(researcher)

def create_curator_agent():
    llm = OllamaLLM(model="qwen3:4b")
    
    def curator(state: GraphState) -> GraphState:
        if state.messages:
            query = state.messages[-1].content
            response = llm.invoke(query)
            state.messages.append(AIMessage(content=response))
        return state
    
    return RunnableLambda(curator)

def create_analyst_agent():
    llm = OllamaLLM(model="qwen3:4b")
    
    def analyst(state: GraphState) -> GraphState:
        if state.messages:
            query = state.messages[-1].content
            response = llm.invoke(query)
            state.messages.append(AIMessage(content=response))
        return state
    
    return RunnableLambda(analyst)

def create_kc_tagger_agent():
    """Agent 4: KC Classifier - Classifies knowledge components using KLI framework"""
    llm = OllamaLLM(model="qwen3:4b")
    
    def kc_tagger(state: GraphState) -> GraphState:
        if state.messages:
            # Get the curator and analyst responses
            curator_summary = ""
            analyst_output = ""
            
            # Extract responses from previous agents
            for i, msg in enumerate(state.messages):
                if hasattr(msg, 'content') and "HumanMessage" not in type(msg).__name__:
                    if i == 1:  # Curator response
                        curator_summary = msg.content[:300] + "..."
                    elif i == 2:  # Analyst response
                        analyst_output = msg.content[:300] + "..."
            
            # Use the improved KC Classifier prompt
            kc_classifier_prompt = f"""
You are a learning science expert helping classify educational content using the KLI framework.

You will be given:
1. A short *concept summary* (e.g., from a researcher or curator agent)
2. A *factual or analytical statement* (e.g., from an analyst agent)

Your task:
✅ Identify the type of knowledge component (KC) this represents.
✅ Identify the dominant learning process a student must engage in to master it.

Possible values:

**KC Types:**
- Factual: A specific definition, term, or data point.
- Conceptual: A relationship or principle that connects multiple ideas.
- Procedural: A step-by-step method, algorithm, or technique.
- Strategic: A higher-order skill for applying knowledge in new or complex contexts.

**Learning Processes (KLI Dimensions):**
- Memory & Fluency: Requires recall and speed.
- Induction & Refinement: Requires generalizing patterns and adjusting understanding.
- Understanding & Sense-Making: Requires building coherent mental models.
- Strategic Application: Requires applying knowledge to unfamiliar tasks.

---

Respond in this exact JSON format:
{{
  "kc_type": "Conceptual",
  "learning_process": "Understanding & Sense-Making"
}}

Do NOT add explanations or modify field names.

---

Concept Summary:
{curator_summary}

Factual Detail:
{analyst_output}
"""
            
            response = llm.invoke(kc_classifier_prompt)
            state.messages.append(AIMessage(content=response))
        return state
    
    return RunnableLambda(kc_tagger)

def build_graph():
    """Build and compile the LangGraph pipeline"""
    graph = StateGraph(GraphState)
    
    graph.add_node("researcher", create_researcher_agent())
    graph.add_node("curator", create_curator_agent())
    graph.add_node("analyst", create_analyst_agent())
    graph.add_node("kc_tagger", create_kc_tagger_agent())
    
    graph.set_entry_point("researcher")
    graph.add_edge("researcher", "curator")
    graph.add_edge("curator", "analyst")
    graph.add_edge("analyst", "kc_tagger")
    graph.add_edge("kc_tagger", END)
    
    return graph.compile()

def process_chunks_for_knowledge_graph():
    """Process PDF chunks through LangGraph agents to extract knowledge"""
    
    print("🧠 Knowledge Graph Pipeline Starting...")
    print("=" * 50)
    
    # Load the chunks
    try:
        with open("ostep_chunks.json", "r") as f:
            docs = json.load(f)
        print(f"✅ Loaded {len(docs)} chunks from ostep_chunks.json")
    except FileNotFoundError:
        print("❌ Error: ostep_chunks.json not found. Run pdf_loader.py first.")
        return
    
    # Build the LangGraph pipeline
    try:
        app = build_graph()
        print("✅ LangGraph pipeline compiled successfully")
    except Exception as e:
        print(f"❌ Error compiling LangGraph: {e}")
        return
    
    # Process chunks and extract knowledge
    knowledge_extracts = []
    
    for i, doc in enumerate(docs[:5]):  # Start with first 5 chunks for testing
        chunk = doc["content"]
        print(f"\n=== Processing Chunk {i+1}/{len(docs[:5])} ===")
        print(f"📄 Chunk preview: {chunk[:200]}...")
        
        try:
            # Prepare the state for LangGraph
            state = {"messages": [HumanMessage(content=chunk)]}
            result = app.invoke(state)
            
            # Extract knowledge from agent responses with KLI classification
            chunk_knowledge = {
                "chunk_id": i + 1,
                "original_content": chunk[:500] + "...",  # Truncate for storage
                "agent_responses": [],
                "kli_classification": {}
            }
            
            # Extract responses from each agent
            researcher_response = ""
            curator_response = ""
            analyst_response = ""
            kc_classification = {}
            
            for msg in result["messages"]:
                if hasattr(msg, 'content'):
                    agent_type = type(msg).__name__
                    response = msg.content
                    
                    chunk_knowledge["agent_responses"].append({
                        "agent_type": agent_type,
                        "response": response
                    })
                    
                    # Store responses for KLI processing
                    if "HumanMessage" not in agent_type:
                        if len(chunk_knowledge["agent_responses"]) == 2:  # First AI response
                            researcher_response = response
                        elif len(chunk_knowledge["agent_responses"]) == 3:  # Second AI response
                            curator_response = response
                        elif len(chunk_knowledge["agent_responses"]) == 4:  # Third AI response
                            analyst_response = response
                        elif len(chunk_knowledge["agent_responses"]) == 5:  # KC Tagger response
                            kc_classification = parse_kc_classification(response)
                    
                    print(f"🤖 {agent_type}: {response[:300]}...")
            
            # Add KLI classification to the knowledge extract
            chunk_knowledge["kli_classification"] = kc_classification
            chunk_knowledge["researcher_summary"] = researcher_response[:200] + "..." if researcher_response else ""
            chunk_knowledge["curator_summary"] = curator_response[:200] + "..." if curator_response else ""
            chunk_knowledge["analyst_output"] = analyst_response[:200] + "..." if analyst_response else ""
            
            knowledge_extracts.append(chunk_knowledge)
            print(f"✅ Chunk {i+1} processed successfully")
            
        except Exception as e:
            print(f"❌ Error processing chunk {i+1}: {e}")
            continue
    
    # Save extracted knowledge
    try:
        with open("knowledge_extracts.json", "w") as f:
            json.dump(knowledge_extracts, f, indent=2)
        print(f"\n💾 Saved {len(knowledge_extracts)} knowledge extracts to knowledge_extracts.json")
    except Exception as e:
        print(f"❌ Error saving knowledge extracts: {e}")
    
    print("\n🎯 Knowledge Graph Pipeline Complete!")
    print("=" * 50)
    return knowledge_extracts

if __name__ == "__main__":
    knowledge_extracts = process_chunks_for_knowledge_graph() 