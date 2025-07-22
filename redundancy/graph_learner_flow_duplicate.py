# Connect to Neo4j
from neo4j import GraphDatabase
from graph.config import NEO4J_URI, NEO4J_AUTH

driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

def insert_course(course_id: str, course_name: str):
    """
    Insert a Course node
    """
    with driver.session() as session:
        session.run("""
            MERGE (:Course {id: $course_id, name: $course_name})
        """, course_id=course_id, course_name=course_name)
    print(f"✅ Inserted course {course_id}")

def link_course_to_los(course_id: str, lo_names: list):
    """
    Link Course to its LearningObjectives
    """
    with driver.session() as session:
        for lo in lo_names:
            session.run("""
                MATCH (c:Course {id: $course_id}), (lo:LearningObjective {name: $lo})
                MERGE (c)-[:HAS_LO]->(lo)
            """, course_id=course_id, lo=lo)
    print(f"✅ Linked {len(lo_names)} LOs to course {course_id}")

def insert_learner(learner_id: str, name: str):
    """
    Create a Learner node
    """
    with driver.session() as session:
        session.run("""
            MERGE (:Learner {id: $learner_id, name: $name})
        """, learner_id=learner_id, name=name)
    print(f"✅ Inserted learner {name} [{learner_id}]")

def link_learner_to_course(learner_id: str, course_id: str):
    """
    Link learner to course
    """
    with driver.session() as session:
        session.run("""
            MATCH (l:Learner {id: $learner_id}), (c:Course {id: $course_id})
            MERGE (l)-[:ENROLLED_IN]->(c)
        """, learner_id=learner_id, course_id=course_id)
    print(f"✅ Enrolled learner {learner_id} in course {course_id}")

def create_personalized_lo_chain(learner_id: str, course_id: str, lo_sequence: list):
    """
    Build a personalized LO path for a learner in a course
    """
    chain_id = f"{learner_id}_{course_id}_path"
    with driver.session() as session:
        # Create personalized chain node
        session.run("""
            MERGE (:PersonalizedLOChain {id: $chain_id, learner_id: $learner_id, course_id: $course_id})
        """, chain_id=chain_id, learner_id=learner_id, course_id=course_id)

        # Link to learner
        session.run("""
            MATCH (l:Learner {id: $learner_id}), (p:PersonalizedLOChain {id: $chain_id})
            MERGE (l)-[:HAS_PATH]->(p)
        """, learner_id=learner_id, chain_id=chain_id)

        # Connect sequential LOs in path
        for i, lo in enumerate(lo_sequence):
            session.run("""
                MATCH (p:PersonalizedLOChain {id: $chain_id}),
                    (lo:LearningObjective {name: $lo})
                MERGE (p)-[:FOLLOWS]->(lo)
            """, chain_id=chain_id, lo=lo)

            if i < len(lo_sequence) - 1:
                lo_next = lo_sequence[i+1]
                session.run("""
                    MATCH (a:LearningObjective {name: $lo}),
                        (b:LearningObjective {name: $lo_next})
                    MERGE (a)-[:NEXT]->(b)
                """, lo=lo, lo_next=lo_next)

    print(f"✅ Created personalized LO chain for {learner_id} in course {course_id}")