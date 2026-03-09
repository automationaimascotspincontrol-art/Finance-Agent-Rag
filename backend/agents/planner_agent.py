from llm.llm_router import call_llm
import os

def run_planner_agent(state: dict):
    query = state.get("query", "")
    prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/planner_prompt.txt")
    with open(prompt_path, "r") as f:
        prompt = f.read().replace("{query}", query)
    plan = call_llm(prompt, "groq")
    return {"plan": plan}
