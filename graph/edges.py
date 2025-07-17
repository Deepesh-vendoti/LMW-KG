"""
Edge definitions and routing logic for the LangGraph knowledge graph.
"""

from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage


def route_to_agent(state: Dict[str, Any]) -> str:
    """
    Routing logic that returns a valid next node name based on the last message.
    """
    messages = state.get("messages", [])
    print("Messages:", messages)
    
    if not messages:
        result = "researcher"  # fallback if no messages
        print("Routing to:", result)
        return result

    last_message = messages[-1].content.lower()

    if "add" in last_message or "insert" in last_message:
        result = "curator"
    elif "analyze" in last_message or "relationship" in last_message:
        result = "analyst"
    elif "tool" in last_message or "search" in last_message or "lookup" in last_message:
        result = "tools"
    else:
        result = "researcher"
    
    print("Routing to:", result)
    return result


def should_continue(state: Dict[str, Any]) -> bool:
    """
    Determine if the workflow should continue or end.
    """
    messages = state.get("messages", [])
    
    if not messages:
        return False
    
    last_message = messages[-1]
    
    # Continue if the last message is from a human or if we need more processing
    if isinstance(last_message, HumanMessage):
        return True
    
    # End if we've reached a certain number of AI responses
    ai_messages = [msg for msg in messages if isinstance(msg, AIMessage)]
    if len(ai_messages) >= 3:  # Limit to 3 AI responses
        return False
    
    return True


def create_conditional_edge():
    """
    Create a conditional edge that routes based on the current state.
    """
    return route_to_agent


def create_continue_edge():
    """
    Create an edge that determines if the workflow should continue.
    """
    return should_continue


# Edge functions for specific routing scenarios
def route_to_researcher(state: Dict[str, Any]) -> bool:
    """Route specifically to researcher agent."""
    return route_to_agent(state) == "researcher"


def route_to_curator(state: Dict[str, Any]) -> bool:
    """Route specifically to curator agent."""
    return route_to_agent(state) == "curator"


def route_to_analyst(state: Dict[str, Any]) -> bool:
    """Route specifically to analyst agent."""
    return route_to_agent(state) == "analyst"


def route_to_tools(state: Dict[str, Any]) -> bool:
    """Route specifically to tools node."""
    return route_to_agent(state) == "tools" 