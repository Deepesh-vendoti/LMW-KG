from graph.db import insert_lo_kc_lp_im # ✅ make sure db.py is in the same folder or in PYTHONPATH

# 🟦 Inputs for insertion
sample_entries = [
    {
        "lo": "Understand Process Synchronization",
        "kc": "Semaphores & Mutexes",
        "learning_process": "Understanding",
        "recommended_instruction": "Worked Example Comparison"
    },
    {
        "lo": "Apply Deadlock Prevention",
        "kc": "Banker's Algorithm",
        "learning_process": "Fluency",
        "recommended_instruction": "Spaced Retrieval Practice"
    },
    {
        "lo": "Master File Management",
        "kc": "Inode Structure",
        "learning_process": "Memory",
        "recommended_instruction": "Retrieval Practice"
    },
    {
        "lo": "Understand Virtual Memory",
        "kc": "Paging & Segmentation",
        "learning_process": "Understanding",
        "recommended_instruction": "Concept Mapping"
    },
    {
        "lo": "Evaluate Scheduling Policies",
        "kc": "Multi-level Feedback Queues",
        "learning_process": "Strategic Thinking",
        "recommended_instruction": "Decision-based Scenarios"
    },
    {
        "lo": "Design Memory Allocation",
        "kc": "Buddy System",
        "learning_process": "Problem Solving",
        "recommended_instruction": "Guided Project Work"
    },
    {
        "lo": "Grasp Disk Scheduling",
        "kc": "SCAN vs C-SCAN Algorithms",
        "learning_process": "Comparison",
        "recommended_instruction": "Venn Diagram Exercises"
    },
    {
        "lo": "Analyze I/O Management",
        "kc": "Interrupt Handling",
        "learning_process": "Conceptual",
        "recommended_instruction": "Visual Simulation"
    },
    {
        "lo": "Understand User Authentication",
        "kc": "Access Control Lists (ACLs)",
        "learning_process": "Procedural",
        "recommended_instruction": "Step-by-Step Demonstration"
    },
    {
        "lo": "Implement Shell Scripting",
        "kc": "Bash Conditional Logic",
        "learning_process": "Procedural Fluency",
        "recommended_instruction": "Worked Examples with Scaffolded Practice"
    }
]

# 🚀 Run the insertion
insert_lo_kc_lp_im(sample_entries)