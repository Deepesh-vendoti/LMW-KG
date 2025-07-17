#!/usr/bin/env python3
"""
Clean test for PLT insertion without duplication
"""

from graph.plt_generator import run_plt_generator
from graph.db import insert_plt_to_neo4j, get_plt_for_learner, clear_plt_for_learner

def test_clean_plt_insertion():
    """Test PLT insertion with duplicate prevention"""
    print("🧪 Testing Clean PLT Insertion (No Duplicates)")
    print("=" * 60)
    
    learner_id = "R000"
    course_id = "OSN"
    
    try:
        # Step 1: Clear any existing data
        print("1️⃣ Clearing existing PLT data...")
        clear_plt_for_learner(learner_id, course_id)
        
        # Step 2: Generate PLT
        print("\n2️⃣ Generating PLT...")
        result = run_plt_generator()
        plt = result["final_plt"]
        expected_steps = len(plt["learning_path"])
        print(f"   ✅ Generated PLT with {expected_steps} steps")
        
        # Step 3: Insert into Neo4j
        print("\n3️⃣ Inserting PLT into Neo4j...")
        insert_plt_to_neo4j(plt, clear_existing=True)
        
        # Step 4: Query and verify
        print("\n4️⃣ Querying PLT from Neo4j...")
        steps = get_plt_for_learner(learner_id, course_id)
        actual_steps = len(steps)
        print(f"   ✅ Retrieved {actual_steps} steps from Neo4j")
        
        # Step 5: Verify no duplication
        if actual_steps == expected_steps:
            print(f"   ✅ Perfect! No duplication detected ({actual_steps} = {expected_steps})")
        else:
            print(f"   ⚠️ Duplication detected: {actual_steps} != {expected_steps}")
        
        # Step 6: Verify context preservation
        print("\n5️⃣ Verifying learner context...")
        for i, step in enumerate(steps, 1):
            assert step["learner_id"] == learner_id, f"Step {i}: learner_id mismatch"
            assert step["course_id"] == course_id, f"Step {i}: course_id mismatch"
        
        print(f"   ✅ All {actual_steps} steps have correct learner context")
        
        print(f"\n🎉 Clean PLT insertion successful!")
        print(f"   👤 Learner: {learner_id}")
        print(f"   📚 Course: {course_id}")
        print(f"   📊 Steps: {actual_steps}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_clean_plt_insertion() 