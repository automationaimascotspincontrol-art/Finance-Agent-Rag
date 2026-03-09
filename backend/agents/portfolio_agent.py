from llm.llm_router import call_llm
import os
import random

def optimize_mock(tickers: list[str]) -> dict:
    allocations = {}
    remaining = 100.0
    for i, ticker in enumerate(tickers):
        if i == len(tickers) - 1:
            allocations[ticker] = round(remaining, 2)
        else:
            val = round(random.uniform(5.0, remaining/2), 2)
            allocations[ticker] = val
            remaining -= val
    return allocations

def run_portfolio_agent(state: dict):
    query = state.get("query", "")
    prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/portfolio_prompt.txt")
    with open(prompt_path, "r") as f:
        prompt = f.read().replace("{tickers}", query)
    
    # Use real LLM instead of mock
    allocation = call_llm(prompt, "groq")
    return {"portfolio_allocation": allocation}
