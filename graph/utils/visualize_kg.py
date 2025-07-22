#!/usr/bin/env python3
"""
Knowledge Graph Visualization

This script connects to Neo4j, retrieves the knowledge graph,
and visualizes it using NetworkX and Matplotlib.
"""

import sys
import os
from pathlib import Path
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from typing import Dict, Any, List, Optional, Tuple

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.database_connections import get_database_manager
from neo4j import GraphDatabase

# Node type to color mapping
NODE_COLORS = {
    "Course": "#4287f5",  # blue
    "LearningObjective": "#f542a7",  # pink
    "KnowledgeComponent": "#42f5a7",  # green
    "LearningProcess": "#f5a742",  # orange
    "InstructionMethod": "#a742f5",  # purple
    "Resource": "#f54242",  # red
    "Learner": "#42f5f5",  # cyan
    "PersonalizedLearningTree": "#f5f542",  # yellow
}

def get_knowledge_graph_data() -> Tuple[List[Dict], List[Dict]]:
    """
    Retrieve knowledge graph data from Neo4j.
    
    Returns:
        Tuple of (nodes, relationships)
    """
    db_manager = get_database_manager()
    driver = db_manager.get_neo4j_driver()
    
    nodes = []
    relationships = []
    
    try:
        with driver.session() as session:
            # Get all nodes
            result = session.run("""
                MATCH (n)
                RETURN id(n) as id, labels(n) as labels, properties(n) as properties
            """)
            
            for record in result:
                node_id = record["id"]
                labels = record["labels"]
                properties = record["properties"]
                
                nodes.append({
                    "id": node_id,
                    "labels": labels,
                    "properties": properties
                })
            
            # Get all relationships
            result = session.run("""
                MATCH (a)-[r]->(b)
                RETURN id(a) as source, id(b) as target, type(r) as type, properties(r) as properties
            """)
            
            for record in result:
                source = record["source"]
                target = record["target"]
                rel_type = record["type"]
                properties = record["properties"]
                
                relationships.append({
                    "source": source,
                    "target": target,
                    "type": rel_type,
                    "properties": properties
                })
                
        return nodes, relationships
        
    except Exception as e:
        print(f"Error retrieving knowledge graph data: {e}")
        return [], []

def build_networkx_graph(nodes: List[Dict], relationships: List[Dict]) -> nx.DiGraph:
    """
    Build a NetworkX graph from nodes and relationships.
    
    Args:
        nodes: List of node dictionaries
        relationships: List of relationship dictionaries
        
    Returns:
        NetworkX DiGraph
    """
    G = nx.DiGraph()
    
    # Add nodes
    for node in nodes:
        node_id = node["id"]
        labels = node["labels"]
        properties = node["properties"]
        
        # Use first label as node type
        node_type = labels[0] if labels else "Unknown"
        
        # Use name or id as node label
        node_label = properties.get("name", properties.get("id", str(node_id)))
        
        G.add_node(
            node_id, 
            type=node_type, 
            label=node_label,
            properties=properties
        )
    
    # Add edges
    for rel in relationships:
        source = rel["source"]
        target = rel["target"]
        rel_type = rel["type"]
        
        G.add_edge(
            source, 
            target, 
            type=rel_type,
            properties=rel["properties"]
        )
    
    return G

def visualize_graph(G: nx.DiGraph, title: str = "Knowledge Graph", figsize: Tuple[int, int] = (16, 12)):
    """
    Visualize the NetworkX graph using Matplotlib.
    
    Args:
        G: NetworkX DiGraph
        title: Plot title
        figsize: Figure size as (width, height)
    """
    plt.figure(figsize=figsize)
    
    # Use different layouts based on graph size
    if len(G) < 50:
        pos = nx.spring_layout(G, k=0.5, iterations=50)
    else:
        pos = nx.kamada_kawai_layout(G)
    
    # Prepare node colors based on type
    node_colors = []
    for node in G.nodes(data=True):
        node_type = node[1].get("type", "Unknown")
        node_colors.append(NODE_COLORS.get(node_type, "#888888"))
    
    # Draw nodes
    nx.draw_networkx_nodes(
        G, 
        pos, 
        node_color=node_colors,
        node_size=700,
        alpha=0.8
    )
    
    # Draw edges with arrows
    nx.draw_networkx_edges(
        G, 
        pos, 
        arrows=True,
        arrowsize=15,
        width=1.5,
        alpha=0.7
    )
    
    # Draw node labels
    labels = {node: data["label"] for node, data in G.nodes(data=True)}
    nx.draw_networkx_labels(
        G, 
        pos, 
        labels=labels,
        font_size=10,
        font_weight="bold"
    )
    
    # Draw edge labels (relationship types)
    edge_labels = {(u, v): data["type"] for u, v, data in G.edges(data=True)}
    nx.draw_networkx_edge_labels(
        G, 
        pos, 
        edge_labels=edge_labels,
        font_size=8
    )
    
    # Create legend for node types
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color, 
                  markersize=10, label=node_type)
        for node_type, color in NODE_COLORS.items()
        if any(data["type"] == node_type for _, data in G.nodes(data=True))
    ]
    
    plt.legend(handles=legend_elements, loc='upper right')
    plt.title(title, fontsize=16)
    plt.axis("off")
    
    plt.tight_layout()
    plt.show()

def generate_mermaid_diagram(nodes: List[Dict], relationships: List[Dict], max_nodes: int = 50) -> str:
    """
    Generate a Mermaid diagram from nodes and relationships.
    
    Args:
        nodes: List of node dictionaries
        relationships: List of relationship dictionaries
        max_nodes: Maximum number of nodes to include in the diagram
        
    Returns:
        Mermaid diagram string
    """
    # Create a mapping from Neo4j IDs to unique Mermaid IDs
    node_map = {}
    
    # Start the Mermaid graph definition
    mermaid = "graph TD;\n"
    
    # Limit the number of nodes if there are too many
    if len(nodes) > max_nodes:
        print(f"⚠️ Limiting Mermaid diagram to {max_nodes} nodes (out of {len(nodes)})")
        nodes = nodes[:max_nodes]
    
    # Process nodes
    for i, node in enumerate(nodes):
        node_id = node["id"]
        labels = node["labels"]
        properties = node["properties"]
        
        # Create a unique Mermaid ID
        mermaid_id = f"node{i}"
        node_map[node_id] = mermaid_id
        
        # Use first label as node type
        node_type = labels[0] if labels else "Unknown"
        
        # Use name or id as node label
        node_label = properties.get("name", properties.get("id", str(node_id)))
        
        # Add node to Mermaid diagram with style based on type
        mermaid += f'  {mermaid_id}["{node_label}<br/>{node_type}"];\n'
    
    # Process relationships
    for rel in relationships:
        source = rel["source"]
        target = rel["target"]
        rel_type = rel["type"]
        
        # Skip if either node is not in the map (due to limiting)
        if source not in node_map or target not in node_map:
            continue
        
        # Add relationship to Mermaid diagram
        mermaid += f'  {node_map[source]} -->|"{rel_type}"| {node_map[target]};\n'
    
    # Add styling for different node types
    mermaid += "\n  %% Styling\n"
    for node_type, color in NODE_COLORS.items():
        mermaid += f'  classDef {node_type} fill:{color};\n'
    
    # Apply styling to nodes
    mermaid += "\n  %% Apply styling\n"
    for i, node in enumerate(nodes):
        node_id = node["id"]
        labels = node["labels"]
        mermaid_id = node_map[node_id]
        
        # Use first label as node type
        node_type = labels[0] if labels else "Unknown"
        
        # Apply class if it exists in NODE_COLORS
        if node_type in NODE_COLORS:
            mermaid += f'  class {mermaid_id} {node_type};\n'
    
    return mermaid

def visualize_knowledge_graph(title: str = "Knowledge Graph", use_mermaid: bool = False):
    """
    Main function to visualize the knowledge graph.
    
    Args:
        title: Plot title
        use_mermaid: Whether to use Mermaid for visualization
    """
    print("🔄 Retrieving knowledge graph data from Neo4j...")
    nodes, relationships = get_knowledge_graph_data()
    
    if not nodes or not relationships:
        print("❌ No knowledge graph data found. Please generate a knowledge graph first.")
        return
    
    print(f"✅ Retrieved {len(nodes)} nodes and {len(relationships)} relationships")
    
    if use_mermaid:
        print("🔄 Generating Mermaid diagram...")
        mermaid_diagram = generate_mermaid_diagram(nodes, relationships)
        print("📊 Mermaid diagram generated:")
        print("\n" + mermaid_diagram)
        return mermaid_diagram
    else:
        print("🔄 Building graph visualization...")
        G = build_networkx_graph(nodes, relationships)
        
        print("📊 Displaying knowledge graph visualization...")
        visualize_graph(G, title=title)
        
        return G

if __name__ == "__main__":
    visualize_knowledge_graph() 