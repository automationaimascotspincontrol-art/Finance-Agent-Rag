import os
import json
from llm.llm_router import call_llm
from services.market_service import MarketService

def run_risk_agent(state: dict):
    query = state.get("query", "")
    financial_analysis = state.get("financial_analysis", "")
    
    # 1. Fetch SEC filings placeholder via MarketService
    # In a real system, we'd extract the company name first
    extraction_prompt = f"Extract company names or stock symbols from: {query}. Return ONLY a JSON list, e.g. ['TSLA']."
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
    
    sec_filings = {}
    if tickers:
        for t in tickers:
            sec_filings[t] = MarketService.get_sec_filings_placeholder(t)

    # 2. Final Prompting 
    prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/risk_prompt.txt")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r") as f:
            base_prompt = f.read()
    else:
        base_prompt = "Assess risk for {query}."
        
    full_prompt = f"{base_prompt}\n\nAnalysis Context: {financial_analysis}\n\nSEC Filings Found: {json.dumps(sec_filings)}"
    risk = call_llm(full_prompt, "groq")
    return {"risk_score": risk}
