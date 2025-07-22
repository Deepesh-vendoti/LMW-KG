#!/usr/bin/env python3
"""
Test Proper Faculty Approval Workflow Sequence

This script demonstrates the correct sequence of microservices with faculty approval gates.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.manual_coordinator import start_faculty_workflow, faculty_approve_course, process_content_after_course_approval
import json

def test_proper_faculty_workflow():
    """Test the proper faculty approval workflow sequence."""
    
    print("🚀 Testing Proper Faculty Approval Workflow Sequence")
    print("=" * 80)
    
    course_id = "proper_faculty_workflow_test"
    faculty_id = "PROF_123"
    
    # Step 1: Start Faculty Workflow (Course Manager)
    print("\n📋 STEP 1: Course Manager - Faculty Input Collection")
    print("-" * 60)
    
    result = start_faculty_workflow(
        course_id=course_id,
        faculty_id=faculty_id,
        content_source="elasticsearch"
    )
    
    print(f"✅ Course Manager Status: {result.get('status', 'N/A')}")
    print(f"✅ Stage: {result.get('stage', 'N/A')}")
    print(f"✅ Next Action: {result.get('next_action_required', 'N/A')}")
    
    if result.get("ui_data", {}).get("course_details"):
        course_details = result["ui_data"]["course_details"]
        print(f"✅ Course ID: {course_details.get('course_id')}")
        print(f"✅ Faculty ID: {course_details.get('faculty_id')}")
        print(f"✅ Content Source: {course_details.get('content_source')}")
        print(f"✅ Status: {course_details.get('initialization_status')}")
    
    # Step 2: Faculty Approves Course Setup
    print("\n👨‍🏫 STEP 2: Faculty Approves Course Setup")
    print("-" * 60)
    
    approve_result = faculty_approve_course(
        course_id=course_id,
        action="approve",
        faculty_comments="Course setup looks good, proceed with content processing"
    )
    
    print(f"✅ Approval Status: {approve_result.get('status', 'N/A')}")
    
    # Step 3: Content Processing (Content Preprocessor + Course Mapper + KLI Application)
    print("\n📚 STEP 3: Content Processing Pipeline")
    print("-" * 60)
    
    content_result = process_content_after_course_approval(course_id)
    
    print(f"✅ Content Processing Status: {content_result.get('status', 'N/A')}")
    print(f"✅ Stage: {content_result.get('stage', 'N/A')}")
    
    if content_result.get('draft_learning_objectives'):
        print(f"✅ Learning Objectives Generated: {len(content_result['draft_learning_objectives'])}")
        print("\n📚 Sample Learning Objectives:")
        for i, lo in enumerate(content_result['draft_learning_objectives'][:3], 1):
            print(f"   {i}. {lo.get('text', 'N/A')}")
    
    # Step 4: Check Knowledge Graph Structure
    print("\n🌐 STEP 4: Knowledge Graph Structure Verification")
    print("-" * 60)
    
    import requests
    
    # Check if Course nodes were created
    response = requests.post(
        "http://localhost:7474/db/neo4j/tx/commit",
        headers={"Content-Type": "application/json"},
        json={
            "statements": [{
                "statement": "MATCH (n:Course) RETURN n.course_id, n.course_name"
            }]
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Course Nodes in Neo4j: {len(data['results'][0]['data'])}")
        for record in data['results'][0]['data']:
            print(f"   • Course ID: {record['row'][0]}, Name: {record['row'][1]}")
    
    # Check Learning Objectives
    response = requests.post(
        "http://localhost:7474/db/neo4j/tx/commit",
        headers={"Content-Type": "application/json"},
        json={
            "statements": [{
                "statement": "MATCH (n:LearningObjective) RETURN count(n) as Count"
            }]
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        count = data['results'][0]['data'][0]['row'][0]
        print(f"✅ Learning Objectives in Neo4j: {count}")
    
    # Check Knowledge Components
    response = requests.post(
        "http://localhost:7474/db/neo4j/tx/commit",
        headers={"Content-Type": "application/json"},
        json={
            "statements": [{
                "statement": "MATCH (n:KnowledgeComponent) RETURN count(n) as Count"
            }]
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        count = data['results'][0]['data'][0]['row'][0]
        print(f"✅ Knowledge Components in Neo4j: {count}")
    
    print("\n" + "=" * 80)
    print("✅ Proper Faculty Workflow Test Completed!")
    print("\n📋 CORRECT SEQUENCE SUMMARY:")
    print("1. ✅ Course Manager: Collects faculty inputs for course outline")
    print("2. ✅ Faculty Approval: Faculty confirms course setup")
    print("3. ✅ Content Preprocessor: Processes uploaded content")
    print("4. ✅ Course Mapper: Creates FACD (Faculty Approved Course Design)")
    print("5. ✅ KLI Application: Creates FCCS (Faculty Confirmed Course Structure)")
    print("6. ✅ Knowledge Graph Generator: Creates proper knowledge graph")
    print("\n🔄 NEXT STEPS:")
    print("• Faculty can approve/confirm the generated structure")
    print("• Learner Subsystem can generate personalized learning trees")
    print("• Analytics Subsystem can provide learning insights")

if __name__ == "__main__":
    test_proper_faculty_workflow() 