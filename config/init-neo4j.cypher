-- Neo4j Database Initialization Script
-- Run this in Neo4j Browser after starting the database

-- Create constraints
CREATE CONSTRAINT FOR (lo:LearningObjective) REQUIRE lo.id IS UNIQUE;
CREATE CONSTRAINT FOR (kc:KnowledgeComponent) REQUIRE kc.id IS UNIQUE;
CREATE CONSTRAINT FOR (course:Course) REQUIRE course.id IS UNIQUE;
CREATE CONSTRAINT FOR (learner:Learner) REQUIRE learner.id IS UNIQUE;
CREATE CONSTRAINT FOR (plt:PersonalizedLearningTree) REQUIRE plt.id IS UNIQUE;

-- Create indexes for better performance
CREATE INDEX FOR (lo:LearningObjective) ON (lo.course_id);
CREATE INDEX FOR (kc:KnowledgeComponent) ON (kc.course_id);
CREATE INDEX FOR (plt:PersonalizedLearningTree) ON (plt.learner_id);
CREATE INDEX FOR (plt:PersonalizedLearningTree) ON (plt.course_id);

-- Sample data structure (adjust based on your actual data)
CREATE (course:Course {
  id: "cs-101",
  name: "Computer Science Fundamentals",
  description: "Introduction to computer science concepts"
});

CREATE (lo1:LearningObjective {
  id: "lo1",
  name: "Understanding Algorithms",
  text: "Students will understand basic algorithmic concepts",
  description: "Covers sorting, searching, and complexity analysis",
  difficulty_level: "beginner",
  course_id: "cs-101"
});

CREATE (kc1:KnowledgeComponent {
  id: "kc1",
  name: "Sorting Algorithms",
  text: "Fundamental sorting algorithms like bubble sort and merge sort",
  description: "Understanding how different sorting algorithms work",
  type: "concept",
  difficulty: "beginner",
  course_id: "cs-101"
});

-- Create relationships
CREATE (lo1)-[:DECOMPOSED_INTO]->(kc1);
CREATE (course)-[:HAS_LEARNING_OBJECTIVE]->(lo1);
CREATE (course)-[:CONTAINS_KNOWLEDGE_COMPONENT]->(kc1);
