#!/usr/bin/env python3
"""
Knowledge Graph Generator and Visualizer

This script:
1. Generates a sample knowledge graph for a course
2. Stores it in Neo4j
3. Automatically visualizes the knowledge graph with the best available option

Usage:
    python generate_and_visualize_kg.py              # Use all defaults
    python generate_and_visualize_kg.py --course_id COURSE_ID
"""

import sys
import os
import argparse
from pathlib import Path
from typing import Dict, Any, List
import platform

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.database_connections import get_database_manager
from subsystems.content.services.knowledge_graph_generator import KnowledgeGraphGeneratorService
from graph.utils.visualize_kg import visualize_knowledge_graph
from orchestrator.state import UniversalState

def generate_sample_fccs(course_id: str = "OSN") -> Dict[str, Any]:
    """
    Generate a sample Faculty Confirmed Course Structure (FCCS).
    
    Args:
        course_id: Course ID
        
    Returns:
        FCCS dictionary
    """
    course_name = "Operating Systems"
    if course_id != "OSN":
        course_name = f"Course {course_id}"
    
    return {
        "course_id": course_id,
        "course_name": course_name,
        "version": "1.0",
        "learning_objectives": [
            {
                "lo_id": f"{course_id}_LO1",
                "text": "Understand virtual memory concepts and implementation",
                "difficulty": "medium"
            },
            {
                "lo_id": f"{course_id}_LO2",
                "text": "Analyze CPU scheduling algorithms and their trade-offs",
                "difficulty": "hard"
            },
            {
                "lo_id": f"{course_id}_LO3",
                "text": "Implement basic file system operations",
                "difficulty": "medium"
            }
        ],
        "knowledge_components": [
            {
                "kc_id": f"{course_id}_KC1",
                "lo_id": f"{course_id}_LO1",
                "text": "Virtual memory mapping",
                "complexity": "medium"
            },
            {
                "kc_id": f"{course_id}_KC2",
                "lo_id": f"{course_id}_LO1",
                "text": "Page tables and TLB",
                "complexity": "hard"
            },
            {
                "kc_id": f"{course_id}_KC3",
                "lo_id": f"{course_id}_LO2",
                "text": "Round-robin scheduling",
                "complexity": "medium"
            },
            {
                "kc_id": f"{course_id}_KC4",
                "lo_id": f"{course_id}_LO2",
                "text": "Priority-based scheduling",
                "complexity": "hard"
            },
            {
                "kc_id": f"{course_id}_KC5",
                "lo_id": f"{course_id}_LO3",
                "text": "File descriptors",
                "complexity": "easy"
            },
            {
                "kc_id": f"{course_id}_KC6",
                "lo_id": f"{course_id}_LO3",
                "text": "Directory operations",
                "complexity": "medium"
            }
        ],
        "learning_processes": [
            {
                "lp_id": f"{course_id}_LP1",
                "kc_id": f"{course_id}_KC1",
                "type": "conceptual",
                "description": "Understanding virtual memory concepts",
                "complexity": "medium"
            },
            {
                "lp_id": f"{course_id}_LP2",
                "kc_id": f"{course_id}_KC2",
                "type": "analytical",
                "description": "Analyzing page table structures",
                "complexity": "hard"
            },
            {
                "lp_id": f"{course_id}_LP3",
                "kc_id": f"{course_id}_KC3",
                "type": "analytical",
                "description": "Evaluating round-robin scheduling",
                "complexity": "medium"
            },
            {
                "lp_id": f"{course_id}_LP4",
                "kc_id": f"{course_id}_KC4",
                "type": "analytical",
                "description": "Comparing priority scheduling algorithms",
                "complexity": "hard"
            },
            {
                "lp_id": f"{course_id}_LP5",
                "kc_id": f"{course_id}_KC5",
                "type": "practical",
                "description": "Working with file descriptors",
                "complexity": "medium"
            },
            {
                "lp_id": f"{course_id}_LP6",
                "kc_id": f"{course_id}_KC6",
                "type": "practical",
                "description": "Implementing directory operations",
                "complexity": "medium"
            }
        ],
        "instruction_methods": [
            {
                "im_id": f"{course_id}_IM1",
                "lp_id": f"{course_id}_LP1",
                "type": "lecture",
                "description": "Interactive lecture on virtual memory",
                "duration": "60min"
            },
            {
                "im_id": f"{course_id}_IM2",
                "lp_id": f"{course_id}_LP2",
                "type": "simulation",
                "description": "Page table simulation exercise",
                "duration": "45min"
            },
            {
                "im_id": f"{course_id}_IM3",
                "lp_id": f"{course_id}_LP3",
                "type": "case_study",
                "description": "Case study on scheduling algorithms",
                "duration": "30min"
            },
            {
                "im_id": f"{course_id}_IM4",
                "lp_id": f"{course_id}_LP4",
                "type": "problem_solving",
                "description": "Priority scheduling problem set",
                "duration": "45min"
            },
            {
                "im_id": f"{course_id}_IM5",
                "lp_id": f"{course_id}_LP5",
                "type": "coding_exercise",
                "description": "File descriptor coding lab",
                "duration": "60min"
            },
            {
                "im_id": f"{course_id}_IM6",
                "lp_id": f"{course_id}_LP6",
                "type": "project",
                "description": "Directory operations mini-project",
                "duration": "90min"
            }
        ]
    }

def clear_neo4j_database():
    """Clear all data in Neo4j database."""
    db_manager = get_database_manager()
    driver = db_manager.get_neo4j_driver()
    
    try:
        with driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("✅ Cleared all data in Neo4j database")
    except Exception as e:
        print(f"❌ Error clearing Neo4j database: {e}")

def can_display_matplotlib():
    """Check if Matplotlib can display visualizations in the current environment."""
    try:
        # Check if running in a GUI-capable environment
        if platform.system() == "Linux" and "DISPLAY" not in os.environ:
            return False
            
        # Try to import and configure Matplotlib
        import matplotlib
        import matplotlib.pyplot as plt
        
        # Try to create a figure (will fail in headless environments)
        plt.figure()
        plt.close()
        
        return True
    except:
        return False

def main():
    parser = argparse.ArgumentParser(description="Generate and visualize a knowledge graph")
    parser.add_argument("--course_id", default="OSN", help="Course ID (default: OSN)")
    parser.add_argument("--clear_existing", action="store_true", help="Clear existing data before generation")
    parser.add_argument("--output", help="Output file for visualization (default: kg_diagram.md)")
    
    args = parser.parse_args()
    
    print("🚀 Knowledge Graph Generator and Visualizer")
    print("=" * 50)
    
    # Step 1: Clear existing data if requested
    if args.clear_existing:
        print("\n1️⃣ Clearing existing Neo4j data...")
        clear_neo4j_database()
    
    # Step 2: Generate sample FCCS
    print(f"\n2️⃣ Generating sample FCCS for course {args.course_id}...")
    fccs = generate_sample_fccs(args.course_id)
    
    # Step 3: Generate knowledge graph
    print("\n3️⃣ Generating knowledge graph...")
    kg_generator = KnowledgeGraphGeneratorService()
    
    # Create initial state with FCCS
    state = UniversalState()
    state["fccs"] = fccs
    state["fccs_approved"] = True
    
    # Generate knowledge graph
    result_state = kg_generator(state)
    
    if "knowledge_graph" not in result_state:
        print(f"❌ Knowledge graph generation failed: {result_state.get('service_errors', {}).get('knowledge_graph_generator', 'Unknown error')}")
        return 1
    
    knowledge_graph = result_state["knowledge_graph"]
    print(f"✅ Knowledge graph generated with {len(knowledge_graph.get('nodes', []))} nodes and {len(knowledge_graph.get('relationships', []))} relationships")
    
    # Step 4: Visualization with best available option
    print("\n4️⃣ Visualizing knowledge graph...")
    title = f"Knowledge Graph for {args.course_id}"
    
    # Try visualization options in order of preference
    if can_display_matplotlib():
        # Best option: Matplotlib visualization if GUI is available
        print("Using Matplotlib visualization (best option)...")
        visualize_knowledge_graph(title=title, use_mermaid=False)
    else:
        # Fallback: Generate Mermaid diagram
        print("Using Mermaid diagram (fallback option)...")
        mermaid_diagram = visualize_knowledge_graph(title=title, use_mermaid=True)
        
        # Save to file
        output_file = args.output or "kg_diagram.md"
        try:
            with open(output_file, 'w') as f:
                f.write("# " + title + "\n\n")
                f.write("```mermaid\n")
                f.write(mermaid_diagram)
                f.write("\n```\n")
            print(f"✅ Mermaid diagram saved to {output_file}")
        except Exception as e:
            print(f"❌ Error saving Mermaid diagram to file: {e}")
    
    print("\n✅ Knowledge graph generation and visualization completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 