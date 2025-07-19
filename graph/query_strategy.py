"""
Query Strategy Core Logic

This module provides the core logic engine for adaptive learner query handling.
It transforms learner profiles into adaptive query strategies based on:
- Learner classification (Novice, Intermediate, Advanced)
- Intervention strategy (e.g., hints, examples, scaffolded help)
- Delivery format (text, quiz, video, chatbot)
- Prompt packaging for LLM integration

Input PDFs used for logic reference:
- Learner Sub System Decision Tree.pdf
- Decision trees - input variables + mappings.pdf
- Learner profiling - adaptive learning attributes.pdf
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# -- Function 1: Classify Learner Type ------------------------

def classify_learner_type(learner_profile: Dict) -> str:
    """
    Classify learner into a type: Novice, Intermediate, or Advanced.
    
    Input:
        learner_profile: dict with fields like {
            "prior_knowledge_score": int (0–10),
            "attempt_history": int,
            "confusion_count": int,
            "time_spent_minutes": float,
            ...
        }

    Output:
        learner_type: str - "Novice", "Intermediate", "Advanced"
    """
    score = learner_profile.get("prior_knowledge_score", 0)
    attempts = learner_profile.get("attempt_history", 0)
    confusion = learner_profile.get("confusion_count", 0)

    if score < 4 or attempts == 0 or confusion > 5:
        return "Novice"
    elif 4 <= score <= 7 and attempts <= 5:
        return "Intermediate"
    else:
        return "Advanced"

# -- Function 2: Choose Intervention Strategy ------------------

def choose_intervention_strategy(learner_type: str, learner_profile: Dict) -> str:
    """
    Choose the intervention strategy to assist the learner.
    
    Output:
        intervention_strategy: str - e.g., "Hints", "Examples", "Scaffolded", "Minimal Help"
    """
    if learner_type == "Novice":
        return "Scaffolded"
    elif learner_type == "Intermediate":
        return "Examples"
    elif learner_type == "Advanced":
        return "Minimal Help"
    return "Hints"  # default fallback

# -- Function 3: Select Delivery Strategy ----------------------

def select_delivery_strategy(intervention_strategy: str, learner_profile: Dict) -> str:
    """
    Select the most effective delivery strategy.

    Output:
        delivery_strategy: str - e.g., "Quiz", "Text Explanation", "Video", "Chatbot"
    """
    prefers_quiz = learner_profile.get("prefers_quiz", False)
    avg_time_spent = learner_profile.get("time_spent_minutes", 0)

    if prefers_quiz and intervention_strategy in ["Examples", "Minimal Help"]:
        return "Quiz"
    elif avg_time_spent > 15:
        return "Video"
    elif intervention_strategy == "Scaffolded":
        return "Chatbot"
    else:
        return "Text Explanation"

# -- Function 4: Package Prompt Components ----------------------

def get_llm_prompt_components(delivery_strategy: str) -> Dict:
    """
    Convert delivery strategy into LLM-ready components.
    
    Output:
        prompt_components: dict - contains format, tone, structure info
    """
    if delivery_strategy == "Quiz":
        return {
            "format": "MCQ",
            "tone": "challenging",
            "structure": "3 questions + feedback"
        }
    elif delivery_strategy == "Video":
        return {
            "format": "summary + link",
            "tone": "engaging",
            "structure": "overview + deeper sections"
        }
    elif delivery_strategy == "Chatbot":
        return {
            "format": "dialogue",
            "tone": "supportive",
            "structure": "Q&A + follow-up"
        }
    else:  # Default: Text Explanation
        return {
            "format": "paragraph",
            "tone": "clarifying",
            "structure": "concept + example + recap"
        }

# -- Function 5: Generate Strategy Summary ----------------------

def generate_strategy_summary(learner_profile: Dict) -> Dict:
    """
    Helper to return the full strategy output for debugging/tracing.
    """
    learner_type = classify_learner_type(learner_profile)
    intervention = choose_intervention_strategy(learner_type, learner_profile)
    delivery = select_delivery_strategy(intervention, learner_profile)
    prompt = get_llm_prompt_components(delivery)

    return {
        "learner_type": learner_type,
        "intervention": intervention,
        "delivery": delivery,
        "prompt_components": prompt
    }

# -- Main Function: Query Strategy Determination ----------------

def determine_query_strategy(learner_id: str, learner_context: Dict[str, Any], 
                           query_type: str = "standard") -> Dict[str, Any]:
    """
    Main function called by Query Strategy Manager service.
    
    Transforms learner context into adaptive query strategy using decision tree logic.
    
    Args:
        learner_id: Unique learner identifier
        learner_context: Dictionary containing learner profile and context
        query_type: Type of query being processed
        
    Returns:
        Strategy result with adaptive routing decisions
    """
    logger.info(f"Determining query strategy for learner {learner_id}")
    
    try:
        # Extract learner profile from context
        learner_profile = learner_context.get("learner_profile", {})
        
        # If no profile available, use context data as profile
        if not learner_profile:
            learner_profile = learner_context
            
        # Apply decision tree logic
        strategy_summary = generate_strategy_summary(learner_profile)
        
        # Map strategy to query complexity
        complexity_mapping = {
            "Novice": "low",
            "Intermediate": "medium", 
            "Advanced": "high"
        }
        
        # Build comprehensive result
        result = {
            "learner_id": learner_id,
            "strategy": f"adaptive_{strategy_summary['delivery'].lower().replace(' ', '_')}",
            "complexity": complexity_mapping.get(strategy_summary['learner_type'], "medium"),
            "query_type": query_type,
            "decision_tree_analysis": strategy_summary,
            "intervention_strategy": strategy_summary['intervention'],
            "delivery_method": strategy_summary['delivery'],
            "prompt_components": strategy_summary['prompt_components'],
            "recommended_actions": [
                f"Apply {strategy_summary['intervention']} intervention",
                f"Use {strategy_summary['delivery']} delivery method",
                f"Adapt to {strategy_summary['learner_type']} learner level",
                f"Format: {strategy_summary['prompt_components']['format']}"
            ],
            "adaptive_routing": {
                "learner_classification": strategy_summary['learner_type'],
                "support_level": strategy_summary['intervention'],
                "presentation_format": strategy_summary['delivery'],
                "llm_prompt_config": strategy_summary['prompt_components']
            }
        }
        
        logger.info(f"Query strategy determined: {result['strategy']} for {strategy_summary['learner_type']} learner")
        return result
        
    except Exception as e:
        logger.error(f"Error determining query strategy: {e}")
        
        # Fallback to simple strategy
        return {
            "learner_id": learner_id,
            "strategy": "standard_adaptive",
            "complexity": "medium",
            "query_type": query_type,
            "error": str(e),
            "fallback_used": True,
            "recommended_actions": [
                "Use standard adaptive approach",
                "Monitor learner performance",
                "Adjust based on feedback"
            ]
        }

# -- Utility Functions for Integration -------------------------

def get_query_complexity_for_learner(learner_profile: Dict) -> str:
    """Quick utility to get just the complexity level."""
    learner_type = classify_learner_type(learner_profile)
    complexity_mapping = {
        "Novice": "low",
        "Intermediate": "medium",
        "Advanced": "high"
    }
    return complexity_mapping.get(learner_type, "medium")

def get_intervention_for_learner(learner_profile: Dict) -> str:
    """Quick utility to get just the intervention strategy."""
    learner_type = classify_learner_type(learner_profile)
    return choose_intervention_strategy(learner_type, learner_profile)
