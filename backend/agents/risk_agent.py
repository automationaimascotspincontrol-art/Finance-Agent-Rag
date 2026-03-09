import os
import json
from llm.llm_router import call_llm
from services.market_service import MarketService
from services.risk_engine import RiskEngine

def run_risk_agent(state: dict):
    query = state.get("query", "")
    financial_analysis = state.get("financial_analysis", "")
    
    # 1. Guardrail: Check for previous errors
    if state.get("quant_error"):
        return {"risk_score": "Skipped: Missing quantitative signals for risk modeling."}

    # 2. Resolve Tickers
    print("Risk: Identifying assets...")
    extraction_prompt = f"Extract company names or stock symbols from: {query}. Return ONLY a JSON list, e.g. ['TSLA']."
    
    try:
        extraction_res = call_llm(extraction_prompt, "groq")
    except Exception as e:
        return {
            "risk_score": "Error in asset identification.",
            "quant_error": True,
            "error_message": f"LLM Failure (Extraction): {str(e)}"
        }
    
    tickers = []
    try:
        import re
        match = re.search(r"\[.*\]", extraction_res, re.DOTALL)
        if match:
            cleaned = match.group(0).replace("'", '"')
            queries = json.loads(cleaned)
            tickers = MarketService.resolve_global_tickers(queries)
        else:
            queries = [q.strip() for q in extraction_res.split(",") if q.strip()]
            tickers = MarketService.resolve_global_tickers(queries)
    except Exception as e:
        print(f"Risk Extraction Error: {e}")
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
        base_prompt = "Assess risk based on data: {risk_data}. Context: {financial_analysis}"
        
    full_prompt = base_prompt.replace("{risk_data}", json.dumps(risk_data, default=str))
    full_prompt = full_prompt.replace("{financial_analysis}", financial_analysis)
    
    print("Risk: Explaining mathematical risk profiles...")
    try:
        risk_explanation = call_llm(full_prompt, "groq")
    except Exception as e:
        return {
            "risk_score": f"Risk modeling unavailable due to LLM error: {str(e)}",
            "quant_error": True,
            "error_message": f"LLM Failure (Risk): {str(e)}"
        }
    
    return {"risk_score": risk_explanation, "risk_data": risk_data}
