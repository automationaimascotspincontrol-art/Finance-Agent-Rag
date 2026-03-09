from llm.llm_router import call_llm
import os

def run_financial_agent(state: dict):
    prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/financial_prompt.txt")
    with open(prompt_path, "r") as f:
        prompt = f.read()
    
    # Inject research data into the prompt format
    research_data = state.get("research_data", "")
    query = state.get("query", "")
    prompt = prompt.replace("{stock_data}", f"Data for {query}")
    prompt = prompt.replace("{news}", research_data)
    prompt = prompt.replace("{rag_context}", "No additional context.")
    
    analysis = call_llm(prompt, "groq")
    return {"financial_analysis": analysis}
