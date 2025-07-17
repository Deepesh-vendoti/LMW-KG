"""
Personalized Learning Tree (PLT) Agents
Specialized agents for generating personalized learning paths
"""

from langchain_core.runnables import RunnableLambda
from langchain_ollama import OllamaLLM
from graph.db import get_kcs_under_lo, get_best_im_for_kc_lp

# 🤖 Shared Ollama model instance
llm = OllamaLLM(model="qwen3:4b")

# -------------------------------
# 🎯 AGENT 1: Accept Learner Context
# -------------------------------
def accept_learner_context(state: dict) -> dict:
    print("👤 [Accept Learner Context] Executing...")

    if not state.get("learner_id") or not state.get("course_id"):
        raise ValueError("Learner ID and Course ID are required")

    learner_profile = {
        "learning_style": "visual",
        "pace": "moderate",
        "experience_level": "intermediate",
        "preferred_format": "interactive"
    }

    print(f"✅ Accepted learner {state['learner_id']} for course {state['course_id']}")
    return {**state, "learner_profile": learner_profile}

# -------------------------------
# 📊 AGENT 2: Prioritize Learning Objectives
# -------------------------------
def prioritize_learning_objectives(state: dict) -> dict:
    print("📊 [Prioritize Learning Objectives] Executing...")

    priority_order = [
        "Understand VM",
        "Explain Paging",
        "Analyze CPU Sched",
        "Design Access Ctrl",
        "Evaluate OS"
    ]

    prioritized_lo = [
        lo for lo in priority_order if lo in state.get("learning_objectives", [])
    ]

    print(f"✅ Prioritized {len(prioritized_lo)} learning objectives")
    return {**state, "prioritized_lo": prioritized_lo}

# -------------------------------
# 🗺️ AGENT 3: Map KCs for Learning Objectives
# -------------------------------
def map_kcs_for_lo(state: dict) -> dict:
    print("🗺️ [Map KCs for Learning Objectives] Executing...")
    personalized_kcs = []

    for lo in state["prioritized_lo"]:
        try:
            kcs = get_kcs_under_lo(lo)
            if not kcs:
                kcs = get_mock_kcs_for_lo(lo)

            personalized_kcs.extend([
                {"lo": lo, "kc": kc, "priority": "high" if lo == "Understand VM" else "medium"}
                for kc in kcs
            ])
        except Exception as e:
            print(f"⚠️ Warning: Could not fetch KCs for {lo}: {e}")
            kcs = get_mock_kcs_for_lo(lo)
            personalized_kcs.extend([
                {"lo": lo, "kc": kc, "priority": "medium"}
                for kc in kcs
            ])

    print(f"✅ Mapped {len(personalized_kcs)} knowledge components")
    return {**state, "personalized_kcs": personalized_kcs}

# -------------------------------
# 🔄 AGENT 4: Sequence Knowledge Components
# -------------------------------
def sequence_kcs(state: dict) -> dict:
    print("🔄 [Sequence Knowledge Components] Executing...")

    lo_groups = {}
    for kc_item in state["personalized_kcs"]:
        lo = kc_item["lo"]
        lo_groups.setdefault(lo, []).append(kc_item)

    sequenced_kcs = []
    for lo in state["prioritized_lo"]:
        if lo in lo_groups:
            for i, kc_item in enumerate(lo_groups[lo]):
                kc_item["sequence"] = i + 1
                sequenced_kcs.append(kc_item)

    print(f"✅ Sequenced {len(sequenced_kcs)} knowledge components")
    return {**state, "sequenced_kcs": sequenced_kcs}

# -------------------------------
# 🎓 AGENT 5: Match Instruction Methods
# -------------------------------
def match_instruction_methods(state: dict) -> dict:
    print("🎓 [Match Instruction Methods] Executing...")
    instruction_methods = []

    for kc_item in state["sequenced_kcs"]:
        kc_name = kc_item["kc"]
        try:
            im = get_best_im_for_kc_lp(kc_name, "Understanding")
            if im == "No instruction method found.":
                im = get_mock_im_for_kc(kc_name)
        except Exception as e:
            print(f"⚠️ Warning: Could not fetch IM for {kc_name}: {e}")
            im = get_mock_im_for_kc(kc_name)

        kc_item["instruction_method"] = im
        instruction_methods.append(kc_item)

    print(f"✅ Matched instruction methods for {len(instruction_methods)} KCs")
    return {**state, "instruction_methods": instruction_methods}

# -------------------------------
# 📚 AGENT 6: Link Resources
# -------------------------------
def link_resources(state: dict) -> dict:
    print("📚 [Link Resources] Executing...")
    resources = []

    for kc_item in state["instruction_methods"]:
        im = kc_item["instruction_method"]
        res = get_mock_resources_for_im(im)
        kc_item["resources"] = res
        resources.append(kc_item)

    final_plt = {
        "learner_id": state["learner_id"],
        "course_id": state["course_id"],
        "learning_path": resources,
        "total_kcs": len(resources),
        "estimated_duration": "8–12 hours"
    }

    print(f"✅ Linked resources and built final PLT with {len(resources)} KCs")
    return {**state, "resources": resources, "final_plt": final_plt}

# -------------------------------
# 🧪 Mock Data Functions
# -------------------------------
def get_mock_kcs_for_lo(lo_name):
    mock_kcs = {
        "Understand VM": ["Virtual Memory Concept", "Address Translation", "Memory Management"],
        "Evaluate OS": ["Performance Metrics", "System Analysis", "Benchmarking"],
        "Analyze CPU Sched": ["Scheduling Algorithms", "Process Priority", "Context Switching"],
        "Explain Paging": ["Page Tables", "Page Faults", "Memory Mapping"],
        "Design Access Ctrl": ["Authentication", "Authorization", "Security Policies"]
    }
    return mock_kcs.get(lo_name, ["Default KC"])

def get_mock_im_for_kc(kc_name):
    mock_ims = {
        "Virtual Memory Concept": "Use visual diagrams and memory layout examples",
        "Address Translation": "Provide step-by-step worked examples",
        "Memory Management": "Use interactive simulations",
        "Performance Metrics": "Show real-world benchmark comparisons",
        "System Analysis": "Use case studies and system logs",
        "Scheduling Algorithms": "Demonstrate with process timeline diagrams",
        "Page Tables": "Use visual page table walkthroughs",
        "Authentication": "Show practical authentication flows"
    }
    return mock_ims.get(kc_name, "Use worked examples with clear explanations")

def get_mock_resources_for_im(im_description):
    return [{
        "resource_id": f"res_{hash(im_description) % 1000}",
        "name": f"Resource for {im_description[:30]}...",
        "type": "interactive",
        "format": "web",
        "difficulty": "medium"
    }]