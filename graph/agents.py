"""
LangGraph Agents – Modular 7-Agent Pipeline
Each agent loads its prompt from the prompts/ folder
Uses shared OllamaLLM model (qwen3:4b)
"""

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableLambda
from langchain_ollama import OllamaLLM
from graph.state import GraphState  # ✅ safe import


# 📦 Utility: Load prompt text from a file
def load_prompt(filename: str) -> str:
    with open(f"prompts/{filename}", "r") as f:
        return f.read()


# 🤖 Shared Ollama model instance
llm = OllamaLLM(model="qwen3:4b")
# llm = OllamaLLM(model="mistral")


# -------------------------------
# 🧠 AGENT 1: Researcher
# -------------------------------
def create_researcher_agent():
    prompt = load_prompt("researcher.txt")
    def researcher(state: GraphState) -> GraphState:
        print("🔍 [Researcher Agent] Executing...")
        if state.messages:
            query = state.messages[-1].content
            response = llm.invoke(prompt + query)
            state.messages.append(AIMessage(content=response))
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
            response = llm.invoke(prompt + query)
            state.messages.append(AIMessage(content=response))
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
            response = llm.invoke(prompt + query)
            state.messages.append(AIMessage(content=response))
        return state
    return RunnableLambda(instruction_agent)