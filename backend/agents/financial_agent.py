import os
import json
from llm.llm_router import call_llm
from services.market_service import MarketService

def run_financial_agent(state: dict):
    query = state.get("query", "")
    research_data = state.get("research_data", "")
    
    # 1. Extract tickers for fundamentals
    extraction_prompt = f"Extract tickers from: {query}. Return ONLY a JSON list, e.g. ['AAPL', 'MSFT']."
    tickers_res = call_llm(extraction_prompt, "groq")
    try:
        # Simple sanitization
        cleaned = tickers_res.strip()
        if "```" in cleaned:
            cleaned = cleaned.split("```")[1].replace("json", "").strip()
        tickers = json.loads(cleaned)
    except:
        tickers = []

    # 2. Add real fundamentals to prompt
    fundamentals = {}
    if tickers:
        for t in tickers:
            fundamentals[t] = MarketService.get_stock_fundamentals(t)

    # 3. Final prompting
    prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/financial_prompt.txt")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r") as f:
            base_prompt = f.read()
    else:
        base_prompt = "Analyze financial data for {query}. Research context: {research_data}"
    
    prompt = base_prompt.replace("{research_data}", research_data).replace("{query}", query)
    full_prompt = f"{prompt}\n\nReal Market Fundamentals:\n{json.dumps(fundamentals)}"
    analysis = call_llm(full_prompt, "groq")
    
    return {"financial_analysis": analysis}
