import os
import json
from llm.llm_router import call_llm
from services.market_service import MarketService
from services.risk_engine import RiskEngine

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
    
    # 2. Perform Quantitative Risk Modeling
    risk_data = {}
    if tickers:
        prices = MarketService.get_closing_prices(tickers)
        returns = MarketService.calculate_log_returns(prices)
        
        var_cvar = RiskEngine.calculate_var_cvar(returns)
        tail_risk = RiskEngine.analyze_tail_risk(returns)
        correlation = RiskEngine.get_correlation_matrix(returns)
        
        # Combine into institutional risk profile
        for t in tickers:
            risk_data[t] = {
                "metrics": var_cvar.get(t, {}),
                "tail_risk_label": tail_risk.get(t, "Unknown"),
                "correlation": correlation.get(t, {})
            }

    # 3. Final Prompting 
    prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/risk_prompt.txt")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r") as f:
            base_prompt = f.read()
    else:
        base_prompt = "Assess risk for {query}."
        
    full_prompt = f"{base_prompt}\n\nAnalysis Context: {financial_analysis}\n\nQuantitative Risk Profile:\n{json.dumps(risk_data)}"
    risk = call_llm(full_prompt, "groq")
    return {"risk_score": risk}
