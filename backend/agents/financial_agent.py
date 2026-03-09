import os
import json
from llm.llm_router import call_llm
from services.market_service import MarketService

def run_financial_agent(state: dict):
    query = state.get("query", "")
    research_data = state.get("research_data", "")
    
    # 1. Guardrail: Check for previous errors
    if state.get("quant_error"):
        return {"financial_analysis": "Skipped: Incomplete data grounding from quantitative engine."}

    # 2. Extract and Resolve Tickers Globally
    extraction_prompt = f"Extract company names or stock symbols from: {query}. Return ONLY a JSON list, e.g. ['Tesla', 'TCS', 'Bitcoin']."
    extraction_res = call_llm(extraction_prompt, "groq")
    try:
        # Simple sanitization
        cleaned = extraction_res.strip()
        if "```" in cleaned:
            cleaned = cleaned.split("```")[1].replace("json", "").strip()
        queries = json.loads(cleaned)
        tickers = MarketService.resolve_global_tickers(queries)
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
