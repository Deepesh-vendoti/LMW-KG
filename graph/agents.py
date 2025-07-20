"""
LangGraph Agents – Modular 7-Agent Pipeline
Each agent loads its prompt from the prompts/ folder
Uses shared OllamaLLM model (qwen3:4b)
"""

import os
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableLambda
from graph.state import GraphState  # ✅ safe import
from graph.config import get_llm, get_llm_gateway
from utils.llm_gateway import TaskType


# 📦 Utility: Load prompt text from a file
def load_prompt(filename: str) -> str:
    # Check if file exists in stage1 directory first
    stage1_path = f"prompts/stage1/{filename}"
    if os.path.exists(stage1_path):
        with open(stage1_path, "r") as f:
            return f.read()
    # Check if file exists in stage2 directory
    stage2_path = f"prompts/stage2/{filename}"
    if os.path.exists(stage2_path):
        with open(stage2_path, "r") as f:
            return f.read()
    else:
        # Fallback to direct prompts directory
        with open(f"prompts/{filename}", "r") as f:
            return f.read()


# 🤖 Shared Ollama model instance
llm = get_llm()


# -------------------------------
# 🧠 AGENT 1: Researcher
# -------------------------------
def create_researcher_agent():
    prompt = load_prompt("researcher.txt")
    def researcher(state: GraphState) -> GraphState:
        print("🔍 [Researcher Agent] Executing...")
        if state.messages:
            query = state.messages[-1].content
            
            # Use LLM Gateway for knowledge extraction with cost optimization
            try:
                gateway = get_llm_gateway()
                if hasattr(gateway, 'generate'):
                    # Use LLM Gateway for advanced knowledge extraction
                    response = gateway.generate(
                        task_type=TaskType.KNOWLEDGE_EXTRACTION,
                        prompt=prompt + query,
                        constraints={
                            "max_cost": 0.08,
                            "privacy_requirement": "local",
                            "max_latency_ms": 5000
                        }
                    )
                    content = response["content"]
                    print(f"✅ [Researcher] Used LLM Gateway ({response['model_used']}) - Cost: ${response['cost']:.4f}")
                else:
                    # Fallback to basic LLM
                    response = llm.invoke(prompt + query)
                    content = response
                    print("⚠️ [Researcher] Used fallback LLM")
            except Exception as e:
                print(f"⚠️ [Researcher] LLM Gateway failed, using fallback: {e}")
                response = llm.invoke(prompt + query)
                content = response
            
            state.messages.append(AIMessage(content=content))
        return state
    return RunnableLambda(researcher)


# -------------------------------
# 🧾 AGENT 2: LO Generator
# -------------------------------
def create_lo_generator_agent():
    prompt = load_prompt("lo_generator.txt")
    def lo_generator(state: GraphState) -> GraphState:
        print("📝 [LO Generator Agent] Executing...")
        if state.messages:
            query = state.messages[-1].content
            
            # Use LLM Gateway for learning objective generation
            try:
                gateway = get_llm_gateway()
                if hasattr(gateway, 'generate'):
                    # Use LLM Gateway for learning objective generation
                    response = gateway.generate(
                        task_type=TaskType.LEARNING_OBJECTIVE_GENERATION,
                        prompt=prompt + query,
                        constraints={
                            "max_cost": 0.10,
                            "privacy_requirement": "local",
                            "max_latency_ms": 6000
                        }
                    )
                    content = response["content"]
                    print(f"✅ [LO Generator] Used LLM Gateway ({response['model_used']}) - Cost: ${response['cost']:.4f}")
                else:
                    # Fallback to basic LLM
                    response = llm.invoke(prompt + query)
                    content = response
                    print("⚠️ [LO Generator] Used fallback LLM")
            except Exception as e:
                print(f"⚠️ [LO Generator] LLM Gateway failed, using fallback: {e}")
                response = llm.invoke(prompt + query)
                content = response
            
            state.messages.append(AIMessage(content=content))
        return state
    return RunnableLambda(lo_generator)


# -------------------------------
# 📚 AGENT 3: Curator
# -------------------------------
def create_curator_agent():
    prompt = load_prompt("curator.txt")
    def curator(state: GraphState) -> GraphState:
        print("📦 [Curator Agent] Executing...")
        if state.messages:
            query = state.messages[-1].content
            response = llm.invoke(prompt + query)
            state.messages.append(AIMessage(content=response))
        return state
    return RunnableLambda(curator)


# -------------------------------
# 📊 AGENT 4: Analyst
# -------------------------------
def create_analyst_agent():
    prompt = load_prompt("analyst.txt")
    def analyst(state: GraphState) -> GraphState:
        print("📈 [Analyst Agent] Executing...")
        if state.messages:
            query = state.messages[-1].content
            response = llm.invoke(prompt + query)
            state.messages.append(AIMessage(content=response))
        return state
    return RunnableLambda(analyst)


# -------------------------------
# 🧮 AGENT 5: KC Classifier
# -------------------------------
def create_kc_classifier_agent():
    prompt = load_prompt("kc_classifier.txt")
    def kc_classifier(state: GraphState) -> GraphState:
        print("🔢 [KC Classifier Agent] Executing...")
        if state.messages:
            query = state.messages[-1].content
            response = llm.invoke(prompt + query)
            state.messages.append(AIMessage(content=response))
        return state
    return RunnableLambda(kc_classifier)


# -------------------------------
# 🔎 AGENT 6: Learning Process Identifier
# -------------------------------
def create_lp_identifier_agent():
    prompt = load_prompt("lp_identifier.txt")
    def lp_identifier(state: GraphState) -> GraphState:
        print("🧭 [Learning Process Identifier Agent] Executing...")
        if state.messages:
            query = state.messages[-1].content
            response = llm.invoke(prompt + query)
            state.messages.append(AIMessage(content=response))
        return state
    return RunnableLambda(lp_identifier)


# -------------------------------
# 🎓 AGENT 7: Instruction Strategy
# -------------------------------
def create_instruction_agent():
    prompt = load_prompt("instruction_agent.txt")
    def instruction_agent(state: GraphState) -> GraphState:
        print("🎯 [Instruction Strategy Agent] Executing...")
        if state.messages:
            query = state.messages[-1].content
            
            # Use LLM Gateway for instruction method selection
            try:
                gateway = get_llm_gateway()
                if hasattr(gateway, 'generate'):
                    # Use LLM Gateway for instruction method selection
                    response = gateway.generate(
                        task_type=TaskType.INSTRUCTION_METHOD_SELECTION,
                        prompt=prompt + query,
                        constraints={
                            "max_cost": 0.08,
                            "privacy_requirement": "local",
                            "max_latency_ms": 4000
                        }
                    )
                    content = response["content"]
                    print(f"✅ [Instruction Agent] Used LLM Gateway ({response['model_used']}) - Cost: ${response['cost']:.4f}")
                else:
                    # Fallback to basic LLM
                    response = llm.invoke(prompt + query)
                    content = response
                    print("⚠️ [Instruction Agent] Used fallback LLM")
            except Exception as e:
                print(f"⚠️ [Instruction Agent] LLM Gateway failed, using fallback: {e}")
                response = llm.invoke(prompt + query)
                content = response
            
            state.messages.append(AIMessage(content=content))
        return state
    return RunnableLambda(instruction_agent)