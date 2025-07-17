"""
CLI Runner for LangGraph KG Agent Pipelines

Use this script to run either:
- Stage 1 (LO + KC Structuring)
- Stage 2 (Learning Process + Instruction Mapping)
- PLT (Personalized Learning Tree Generation + Neo4j Insertion)

Run via:
    python main.py stage1
    python main.py stage2
    python main.py plt
"""

import sys
from langchain_core.messages import HumanMessage
from graph.graph import build_graph_stage_1, build_graph_stage_2
from graph.plt_generator import run_plt_generator
from graph.db import insert_plt_to_neo4j, get_plt_for_learner

def run_plt_pipeline():
    """Run the complete PLT generation + insertion + query pipeline"""
    learner_id = "R000"
    course_id = "OSN"

    try:
        # Step 1: Generate and insert
        print("1️⃣ Generating Personalized Learning Tree...")
        result = run_plt_generator()
        plt = result["final_plt"]
        print(f"   ✅ Generated PLT with {len(plt['learning_path'])} steps")
        
        print("\n2️⃣ Inserting PLT into Neo4j...")
        insert_plt_to_neo4j(plt, clear_existing=True)
        print("   ✅ Inserted PLT steps into Neo4j (cleared existing data).")

        # Step 2: Query and verify
        print("\n3️⃣ Querying and verifying PLT data...")
        steps = get_plt_for_learner(learner_id, course_id)
        print(f"   ✅ Retrieved {len(steps)} PLT steps from Neo4j.")
        
        print(f"\n4️⃣ PLT Summary for {learner_id} in {course_id}:")
        print("-" * 50)
        for i, step in enumerate(steps, 1):
            print(f"{i:2d}. {step['lo']} → {step['kc']} (Priority: {step['priority']}, Seq: {step['sequence']})")
        
        print(f"\n🎉 PLT Pipeline Complete! Generated and stored {len(steps)} personalized learning steps.")
        
    except Exception as e:
        print(f"❌ PLT Pipeline failed: {e}")
        import traceback
        traceback.print_exc()

def run_stage(stage: str):
    if stage == "stage1":
        print("🧠 Building Stage 1 graph...")
        graph = build_graph_stage_1()
        print("🚀 Running Stage 1 (LO + KC Structuring)...")
        default_input = "Explain process scheduling and memory management in OS."
    elif stage == "stage2":
        print("🧠 Building Stage 2 graph...")
        graph = build_graph_stage_2()
        print("🚀 Running Stage 2 (LP + Instruction)...")
        default_input = "KC: Virtual Memory | Learning Process: Understanding"
    elif stage == "plt":
        print("🌳 Running PLT (Personalized Learning Tree) Generation + Neo4j Insertion...")
        run_plt_pipeline()
        return
    else:
        print("❌ Invalid stage. Use 'stage1', 'stage2', or 'plt'.")
        return

    try:
        user_input = input("\n✏️ Enter input (or press Enter to use default):\n> ").strip()
    except Exception as e:
        print(f"⚠️ Could not read input. Using default. Error: {e}")
        user_input = ""

    if not user_input:
        user_input = default_input

    print(f"\n📨 Input to LangGraph: {user_input}")
    print("⏳ Invoking LangGraph pipeline...")

    try:
        result = graph.invoke({"messages": [HumanMessage(content=user_input)]})
        print("\n✅ Final Output:")
        for msg in result["messages"]:
            print(f"[{msg.type.upper()}] {msg.content}")
    except Exception as e:
        print(f"❌ LangGraph execution failed.\nError: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("❗ Usage: python main.py <stage1 | stage2 | plt>")
    else:
        run_stage(sys.argv[1])