import os
import json
from llm.llm_router import call_llm
from services.portfolio_service import PortfolioService

def run_quant_agent(state: dict):
    query = state.get("query", "")
    
    # 1. Extract tickers using LLM
    extraction_prompt = f"Extract tickers from: {query}. Return ONLY a JSON list, e.g. ['TSLA', 'AMZN']."
    extraction_res = call_llm(extraction_prompt, "groq")
    try:
        cleaned_json = extraction_res.strip()
        if "```json" in cleaned_json:
            cleaned_json = cleaned_json.split("```json")[1].split("```")[0].strip()
        tickers = json.loads(cleaned_json)
    except Exception:
        tickers = []

    if not tickers:
        return {"quant_analysis": "No tickers identified for quantitative analysis."}

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
