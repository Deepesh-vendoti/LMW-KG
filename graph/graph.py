"""
LangGraph Orchestration for Knowledge Graph System

This script defines two LangGraph pipelines for knowledge structuring and instructional design:

Stage 1:
1. Researcher Agent → 2. LO Generator Agent → 3. Curator Agent →
4. Analyst Agent → 5. KC Classifier Agent → END

Stage 2:
6. Learning Process Identifier Agent → 7. Instruction Agent → END

Each stage runs independently and expects a list of HumanMessage(s) as input.

LLM: Ollama (Qwen3:4b)
"""

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

# ✅ Correct import of shared state schema
from graph.state import GraphState

# ✅ Agents from graph.agents
from graph.agents import (
    # Stage 1 agents
    create_researcher_agent,
    create_lo_generator_agent,
    create_curator_agent,
    create_analyst_agent,
    create_kc_classifier_agent,
    # Stage 2 agents
    create_lp_identifier_agent,
    create_instruction_agent
)


# ⚙️ Build Stage 1 LangGraph pipeline
def build_graph_stage_1():
    graph = StateGraph(GraphState)

    graph.add_node("researcher", create_researcher_agent())
    graph.add_node("lo_generator", create_lo_generator_agent())
    graph.add_node("curator", create_curator_agent())
    graph.add_node("analyst", create_analyst_agent())
    graph.add_node("kc_classifier", create_kc_classifier_agent())

    graph.set_entry_point("researcher")
    graph.add_edge("researcher", "lo_generator")
    graph.add_edge("lo_generator", "curator")
    graph.add_edge("curator", "analyst")
    graph.add_edge("analyst", "kc_classifier")
    graph.add_edge("kc_classifier", END)

    return graph.compile()


# ⚙️ Build Stage 2 LangGraph pipeline
def build_graph_stage_2():
    graph = StateGraph(GraphState)

    graph.add_node("lp_identifier", create_lp_identifier_agent())
    graph.add_node("instruction", create_instruction_agent())

    graph.set_entry_point("lp_identifier")
    graph.add_edge("lp_identifier", "instruction")
    graph.add_edge("instruction", END)

    return graph.compile()