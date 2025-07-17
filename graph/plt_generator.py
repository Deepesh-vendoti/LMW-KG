from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END
from graph.agents_plt import (
    accept_learner_context,
    prioritize_learning_objectives,
    map_kcs_for_lo,
    sequence_kcs,
    match_instruction_methods,
    link_resources
)

# ✅ State Schema
class PLTState(TypedDict, total=False):
    learner_id: str
    course_id: str
    learning_objectives: List[str]
    learner_profile: Dict
    prioritized_lo: List[str]
    personalized_kcs: List[Dict]
    sequenced_kcs: List[Dict]
    instruction_methods: List[Dict]
    resources: List[Dict]
    final_plt: Dict

# ✅ Build LangGraph Flow
def build_plt_graph():
    graph = StateGraph(PLTState)

    graph.add_node("AcceptLearner", accept_learner_context)
    graph.add_node("PrioritizeLOs", prioritize_learning_objectives)
    graph.add_node("MapKCs", map_kcs_for_lo)
    graph.add_node("SequenceKCs", sequence_kcs)
    graph.add_node("MatchIMs", match_instruction_methods)
    graph.add_node("LinkResources", link_resources)

    graph.set_entry_point("AcceptLearner")
    graph.add_edge("AcceptLearner", "PrioritizeLOs")
    graph.add_edge("PrioritizeLOs", "MapKCs")
    graph.add_edge("MapKCs", "SequenceKCs")
    graph.add_edge("SequenceKCs", "MatchIMs")
    graph.add_edge("MatchIMs", "LinkResources")
    graph.add_edge("LinkResources", END)

    return graph.compile()

# ✅ Run Entry Point
def run_plt_generator():
    graph = build_plt_graph()

    inputs: PLTState = {
        "learner_id": "R000",
        "course_id": "OSN",
        "learning_objectives": [
            "Understand VM",
            "Evaluate OS",
            "Analyze CPU Sched",
            "Explain Paging",
            "Design Access Ctrl"
        ]
    }

    print("🌳 Generating Personalized Learning Tree (PLT) for Learner R000...")
    print("=" * 60)
    return graph.invoke(inputs)