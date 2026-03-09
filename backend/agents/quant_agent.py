import os
import json
from llm.llm_router import call_llm
from services.portfolio_service import PortfolioService
from services.market_service import MarketService

def run_quant_agent(state: dict):
    query = state.get("query", "")
    
    # 1. Extract and Resolve Tickers Globally
    extraction_prompt = f"Extract company names or stock symbols from: {query}. Return ONLY a JSON list, e.g. ['Tesla', 'TCS', 'Bitcoin']."
    extraction_res = call_llm(extraction_prompt, "groq")
    try:
        cleaned = extraction_res.strip()
        if "```" in cleaned:
            cleaned = cleaned.split("```")[1].replace("json", "").strip()
        queries = json.loads(cleaned)
        # Resolve names like "Tesla" to "TSLA" or "TCS" to "TCS.NS"
        tickers = MarketService.resolve_global_tickers(queries)
    except:
        tickers = []

    if not tickers:
        return {"quant_analysis": "No assets identified for quantitative analysis."}

    # 2. Calculate Real Metrics via PortfolioService
    metrics_dict = PortfolioService.get_risk_metrics(tickers)
    
    # 3. Explain Metrics via LLM
    prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/quant_prompt.txt")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r") as f:
            base_prompt = f.read()
    else:
        base_prompt = "Analyze these metrics: {quant_data}"
    
    analysis_prompt = base_prompt.replace("{quant_data}", json.dumps(metrics_dict))
    analysis_prompt = analysis_prompt.replace("{query}", query)
    
    analysis = call_llm(analysis_prompt, "groq")
    
    return {
        "quant_analysis": analysis,
        "quant_data": metrics_dict
    }
