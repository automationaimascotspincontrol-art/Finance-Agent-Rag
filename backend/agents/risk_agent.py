from llm.llm_router import call_llm
import os

def run_risk_agent(state: dict):
    prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/risk_prompt.txt")
    with open(prompt_path, "r") as f:
        prompt = f.read()
    
    # Give the risk agent the prior analysis format
    analysis = state.get("financial_analysis", "")
    prompt += f"\n\nContext:\n{analysis}"
    
    score = call_llm(prompt, "groq")
    return {"risk_score": score}
