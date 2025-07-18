from neo4j import GraphDatabase
from typing import Dict, List
from graph.config import NEO4J_URI, NEO4J_AUTH

# 🔌 Neo4j connection (no auth needed)
driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)


def insert_lo_kc_lp_im(data_list: list, parent_topic: str = "Operating Systems"):
    """
    Insert LO → KC → LP → IM relationships into the Neo4j graph database.
    """
    with driver.session() as session:
        for entry in data_list:
            lo = entry.get("lo", "Unspecified LO")
            kc = entry["kc"]
            lp = entry["learning_process"]
            im = entry["recommended_instruction"]

            # 🟢 Merge LearningObjective
            session.run("""
                MERGE (lo:LearningObjective {id: $lo})
                SET lo.text = $lo
            """, lo=lo)

            # 🟢 Merge KnowledgeComponent
            session.run("""
                MERGE (kc:KnowledgeComponent {id: $kc})
                SET kc.text = $kc
            """, kc=kc)

            # 🔵 Merge LearningProcess
            session.run("""
                MERGE (lp:LearningProcess {id: $lp})
                SET lp.type = $lp
            """, lp=lp)

            # 🟣 Merge InstructionMethod
            session.run("""
                MERGE (im:InstructionMethod {id: $im})
                SET im.description = $im
            """, im=im)

            # 🔗 LO → KC
            session.run("""
                MATCH (lo:LearningObjective {id: $lo}), (kc:KnowledgeComponent {id: $kc})
                MERGE (lo)-[:DECOMPOSED_INTO]->(kc)
            """, lo=lo, kc=kc)

            # 🔗 KC → LP
            session.run("""
                MATCH (kc:KnowledgeComponent {id: $kc}), (lp:LearningProcess {id: $lp})
                MERGE (kc)-[:REQUIRES]->(lp)
            """, kc=kc, lp=lp)

            # 🔗 LP → IM
            session.run("""
                MATCH (lp:LearningProcess {id: $lp}), (im:InstructionMethod {id: $im})
                MERGE (lp)-[:BEST_SUPPORTED_BY]->(im)
            """, lp=lp, im=im)

    print(f"✅ Inserted {len(data_list)} LO → KC → LP → IM entries under topic '{parent_topic}'")


def link_learning_objectives_in_sequence(lo_sequence: list):
    """
    Create :NEXT relationships between LearningObjectives to indicate sequential order.
    """
    with driver.session() as session:
        for i in range(len(lo_sequence) - 1):
            lo1 = lo_sequence[i]
            lo2 = lo_sequence[i + 1]
            session.run("""
                MATCH (a:LearningObjective {id: $lo1})
                MATCH (b:LearningObjective {id: $lo2})
                MERGE (a)-[:NEXT]->(b)
            """, lo1=lo1, lo2=lo2)

    print(f"✅ Linked {len(lo_sequence) - 1} LearningObjectives sequentially")


def get_kcs_under_lo(lo_name: str) -> list:
    """
    Given a Learning Objective name, return a list of linked Knowledge Components.
    """
    with driver.session() as session:
        result = session.run("""
            MATCH (lo:LearningObjective {id: $lo_name})-[:DECOMPOSED_INTO]->(kc:KnowledgeComponent)
            RETURN COALESCE(kc.text, kc.name) AS kc_name
        """, lo_name=lo_name)
        return [record["kc_name"] for record in result]


def get_best_im_for_kc_lp(kc_name: str, lp_type: str) -> str:
    """
    Given a Knowledge Component and a Learning Process, return the best Instruction Method description.
    """
    with driver.session() as session:
        result = session.run("""
            MATCH (kc:KnowledgeComponent {id: $kc_name})-[:REQUIRES]->(lp:LearningProcess {id: $lp_type})
                -[:BEST_SUPPORTED_BY]->(im:InstructionMethod)
            RETURN im.description AS im_desc
        """, kc_name=kc_name, lp_type=lp_type)
        record = result.single()
        return record["im_desc"] if record else "No instruction method found."


def insert_resource_for_im(im_description: str, resources: list):
    """
    Link resources to an InstructionMethod node via :USES relationship.
    Each resource is a dict with: 'resource_id', 'name', 'type', 'format', 'difficulty'
    """
    with driver.session() as session:
        for resource in resources:
            resource_id = resource["resource_id"]
            name = resource["name"]
            type_ = resource.get("type", "lesson")
            format_ = resource.get("format", "text")
            difficulty = resource.get("difficulty", "medium")

            # 🟡 Merge Resource node
            session.run("""
                MERGE (r:Resource {resource_id: $resource_id})
                SET r.name = $name,
                    r.type = $type,
                    r.format = $format,
                    r.difficulty = $difficulty
            """, resource_id=resource_id, name=name, type=type_, format=format_, difficulty=difficulty)

            # 🔗 Link to InstructionMethod
            session.run("""
                MATCH (im:InstructionMethod {id: $im_description}),
                    (r:Resource {resource_id: $resource_id})
                MERGE (im)-[:USES]->(r)
            """, im_description=im_description, resource_id=resource_id)

    print(f"✅ Linked {len(resources)} resources to InstructionMethod '{im_description}'")


def clear_plt_for_learner(learner_id: str, course_id: str = None):
    """
    Clear existing PLT data for a specific learner and course to prevent duplicates.
    
    Args:
        learner_id: The learner ID to clear data for
        course_id: Optional course ID to filter by (if None, clears all courses for learner)
    """
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    
    with driver.session() as session:
        if course_id:
            # Clear specific learner + course combination
            result = session.run("""
                MATCH (n:PersonalizedLearningStep) 
                WHERE n.learner_id = $learner_id AND n.course_id = $course_id
                DELETE n
                RETURN count(n) as deleted_count
            """, learner_id=learner_id, course_id=course_id)
        else:
            # Clear all courses for the learner
            result = session.run("""
                MATCH (n:PersonalizedLearningStep) 
                WHERE n.learner_id = $learner_id
                DELETE n
                RETURN count(n) as deleted_count
            """, learner_id=learner_id)
        
        deleted_count = result.single()["deleted_count"]
        print(f"🧹 Cleared {deleted_count} existing PLT nodes for {learner_id}" + (f" in {course_id}" if course_id else ""))
    
    driver.close()

def insert_plt_to_neo4j(plt: dict, neo4j_uri="bolt://localhost:7687", clear_existing=True):
    """
    Insert a Personalized Learning Tree (PLT) into Neo4j for a given learner and course.
    
    Creates :PersonalizedLearningStep nodes with all properties for easy querying:
    - learner_id, course_id, lo, kc, priority, sequence, instruction_method
    
    Args:
        plt: PLT dictionary containing learner_id, course_id, and learning_path
        neo4j_uri: Neo4j connection URI
        user: Neo4j username
        password: Neo4j password
        clear_existing: Whether to clear existing PLT data before inserting (prevents duplicates)
    
    Usage:
        result = run_plt_generator()
        insert_plt_to_neo4j(result["final_plt"])
    """
    # 🛡️ Safeguard: Verify PLT structure has required fields
    if "learner_id" not in plt or "course_id" not in plt:
        raise ValueError("PLT must contain 'learner_id' and 'course_id' fields")
    
    if "learning_path" not in plt:
        raise ValueError("PLT must contain 'learning_path' field")
    
    # 🧹 Clear existing PLT data to prevent duplicates
    if clear_existing:
        clear_plt_for_learner(plt["learner_id"], plt["course_id"])
    
    driver = GraphDatabase.driver(neo4j_uri, auth=None)

    with driver.session() as session:
        for step in plt["learning_path"]:
            # 🛡️ Safeguard: Verify each step has required fields
            if "lo" not in step or "kc" not in step or "instruction_method" not in step:
                raise ValueError(f"PLT step missing required fields: {step}")
            
            session.write_transaction(
                _create_step_node,
                plt["learner_id"],
                plt["course_id"],
                step
            )

    driver.close()
    print(f"✅ Inserted PLT for learner {plt['learner_id']} in course {plt['course_id']} with {len(plt['learning_path'])} learning steps")


def _create_step_node(tx, learner_id, course_id, step):
    """
    Create a single PersonalizedLearningStep node with all properties.
    """
    # 🛡️ Safeguard: Ensure all required properties are present
    if not learner_id or not course_id:
        raise ValueError("learner_id and course_id must be provided")
    
    # Set default values for optional fields
    priority = step.get("priority", "medium")
    sequence = step.get("sequence", -1)
    
    tx.run("""
        CREATE (s:PersonalizedLearningStep {
            learner_id: $learner_id,
            course_id: $course_id,
            lo: $lo,
            kc: $kc,
            priority: $priority,
            sequence: $sequence,
            instruction_method: $instruction_method
        })
    """, learner_id=learner_id,
        course_id=course_id,
        lo=step["lo"],
        kc=step["kc"],
        priority=priority,
        sequence=sequence,
        instruction_method=step["instruction_method"])


def get_plt_for_learner(learner_id: str, course_id: str = None) -> list:
    """
    Query Personalized Learning Tree data for a specific learner.
    
    Args:
        learner_id: The learner ID to query for
        course_id: Optional course ID to filter by
    
    Returns:
        List of dictionaries containing PLT step data
    """
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    
    with driver.session() as session:
        if course_id:
            # Query for specific learner and course
            result = session.run("""
                MATCH (n:PersonalizedLearningStep) 
                WHERE n.learner_id = $learner_id AND n.course_id = $course_id
                RETURN n ORDER BY n.sequence
            """, learner_id=learner_id, course_id=course_id)
        else:
            # Query for all courses for the learner
            result = session.run("""
                MATCH (n:PersonalizedLearningStep) 
                WHERE n.learner_id = $learner_id
                RETURN n ORDER BY n.course_id, n.sequence
            """, learner_id=learner_id)
        
        steps = []
        for record in result:
            node = record["n"]
            steps.append({
                "learner_id": node.get("learner_id"),
                "course_id": node.get("course_id"),
                "lo": node.get("lo"),
                "kc": node.get("kc"),
                "priority": node.get("priority"),
                "sequence": node.get("sequence"),
                "instruction_method": node.get("instruction_method")
            })
    
    driver.close()
    return steps

def insert_course_kg_to_neo4j(course_kg: dict):
    """
    Inserts a full course-level Knowledge Graph (LO → KC → IM → Resource) into Neo4j.
    Does not affect personalized PLTs.
    
    Expected structure:
    {
        "course_id": "OSN",
        "course_name": "Operating Systems",
        "learning_objectives": [
            {
                "id": "LO001",
                "text": "Understand Virtual Memory",
                "kcs": [
                    {
                        "id": "KC001",
                        "text": "Virtual Memory Concept"
                    }
                ]
            }
        ],
        "instruction_methods": [
            {
                "kc_id": "KC001",
                "method": "Use visual diagrams and memory layout examples",
                "type": "Visualization"
            }
        ],
        "resources": [
            {
                "method": "Use visual diagrams and memory layout examples",
                "url": "https://example.com/vm-diagrams",
                "title": "Virtual Memory Visualization"
            }
        ]
    }
    
    Resulting KG Layout:
    (:Course)-[:HAS_LO]->(:LearningObjective)-[:HAS_KC]->(:KC)
    (:KC)-[:DELIVERED_BY]->(:IM)-[:USES_RESOURCE]->(:Resource)
    (:IM)-[:ALIGNS_WITH]->(:LearningProcess)
    """
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

    def _create_course_kg(tx, course):
        course_id = course["course_id"]
        course_name = course.get("course_name", "")

        tx.run(
            "MERGE (c:Course {id: $course_id}) "
            "SET c.name = $course_name",
            course_id=course_id,
            course_name=course_name,
        )

        for lo in course["learning_objectives"]:
            lo_id = lo["id"]
            lo_text = lo["text"]
            tx.run(
                "MERGE (lo:LearningObjective {id: $lo_id}) "
                "SET lo.text = $lo_text "
                "WITH lo "
                "MATCH (c:Course {id: $course_id}) "
                "MERGE (c)-[:HAS_LO]->(lo)",
                lo_id=lo_id,
                lo_text=lo_text,
                course_id=course_id,
            )

            for kc in lo["kcs"]:
                kc_id = kc["id"]
                kc_text = kc["text"]
                tx.run(
                    "MERGE (kc:KnowledgeComponent {id: $kc_id}) "
                    "SET kc.text = $kc_text "
                    "WITH kc "
                    "MATCH (lo:LearningObjective {id: $lo_id}) "
                    "MERGE (lo)-[:HAS_KC]->(kc)",
                    kc_id=kc_id,
                    kc_text=kc_text,
                    lo_id=lo_id,
                )

    def _create_ims_and_resources(tx, ims, resources):
        # Create Instruction Methods and link to Knowledge Components
        for im in ims:
            tx.run(
                "MATCH (kc:KnowledgeComponent {id: $kc_id}) "
                "MERGE (im:InstructionMethod {id: $method}) "
                "SET im.description = $method, im.type = $type "
                "MERGE (kc)-[:DELIVERED_BY]->(im)",
                kc_id=im["kc_id"],
                method=im["method"],
                type=im.get("type", "General"),
            )
        
        # Create Resources and link to Instruction Methods (not Knowledge Components)
        for res in resources:
            tx.run(
                "MATCH (im:InstructionMethod {id: $method}) "
                "MERGE (res:Resource {url: $url}) "
                "SET res.title = $title "
                "MERGE (im)-[:USES_RESOURCE]->(res)",
                method=res["method"],
                url=res["url"],
                title=res.get("title", ""),
            )

    with driver.session() as session:
        session.write_transaction(_create_course_kg, course_kg)
        session.write_transaction(_create_ims_and_resources, course_kg.get("instruction_methods", []), course_kg.get("resources", []))

    driver.close()
    print(f"✅ Inserted course-level KG for {course_kg['course_id']} with {len(course_kg['learning_objectives'])} LOs")