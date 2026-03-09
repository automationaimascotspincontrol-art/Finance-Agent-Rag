from llm.llm_router import call_llm
import os

def run_research_agent(state: dict):
    query = state.get("query", "")
    prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/research_prompt.txt")
    with open(prompt_path, "r") as f:
        prompt = f.read().replace("{query}", query)
    research = call_llm(prompt, "groq")
    return {"research_data": research}
