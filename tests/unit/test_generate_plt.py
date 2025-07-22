from graph.plt_generator import run_plt_generator

if __name__ == "__main__":
    print("🌳 Generating Personalized Learning Tree (PLT) for Learner R000...")
    print("=" * 60)
    
    try:
        result = run_plt_generator()
        
        print("\n✅ Generated Personalized Learning Tree (PLT):")
        print("=" * 60)
        
        # ✅ Corrected dict access
        plt = result["final_plt"]
        
        print(f"👤 Learner ID: {plt['learner_id']}")
        print(f"📚 Course ID: {plt['course_id']}")
        print(f"📊 Total KCs: {plt['total_kcs']}")
        print(f"⏱️ Estimated Duration: {plt['estimated_duration']}")
        
        print(f"\n🛤️ Learning Path ({len(plt['learning_path'])} steps):")
        print("-" * 40)
        
        for i, step in enumerate(plt['learning_path'], 1):
            print(f"\n{i}. Learning Objective: {step['lo']}")
            print(f"   Knowledge Component: {step['kc']}")
            print(f"   Priority: {step.get('priority', 'medium')}")
            print(f"   Sequence: {step.get('sequence', 'N/A')}")
            print(f"   Instruction Method: {step['instruction_method']}")
            
            if step.get('resources'):
                print(f"   📚 Resources: {len(step['resources'])} available")
                for res in step['resources']:
                    print(f"      - {res['name']} ({res['type']}, {res['difficulty']})")
        
        print("\n" + "=" * 60)
        print("🎯 PLT Generation Complete!")
        
    except Exception as e:
        print(f"❌ Error generating PLT: {e}")
        import traceback
        traceback.print_exc()