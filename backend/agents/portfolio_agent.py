import os
import json
from llm.llm_router import call_llm
from services.portfolio_service import PortfolioService

def run_portfolio_agent(state: dict):
    query = state.get("query", "")
    financial_analysis = state.get("financial_analysis", "")
    
    # 1. Extract tickers using LLM
    extraction_prompt = f"""
    Extract the stock ticker symbols from the user query.
    Query: "{query}"
    Return ONLY a JSON list of strings, e.g., ["AAPL", "TSLA"].
    If no tickers are found, return [].
    """
    extraction_res = call_llm(extraction_prompt, "groq")
    try:
        # Basic sanitization for common LLM prefixes
        cleaned_json = extraction_res.strip()
        if "```json" in cleaned_json:
            cleaned_json = cleaned_json.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned_json:
            cleaned_json = cleaned_json.split("```")[1].split("```")[0].strip()
        
        tickers = json.loads(cleaned_json)
    except Exception:
        tickers = []

    if not tickers:
        return {"portfolio_allocation": "No specific tickers identified for optimization."}

    # 2. Extract AI "Views" (Expected Returns) from Financial Analysis
    # This turns text into a mathematical prior for Black-Litterman
    view_prompt = f"""
    Based on the following financial analysis, estimate the expected annual return (as a decimal) for each ticker.
    Analysis: {financial_analysis}
    Tickers: {tickers}
    Return ONLY a JSON dictionary, e.g. {{"AAPL": 0.12, "TSLA": -0.05}}.
    If no view is possible, use 0.05 (5%) as neutral.
    """
    view_res = call_llm(view_prompt, "groq")
    try:
        cleaned_views = view_res.strip()
        if "```" in cleaned_views:
            cleaned_views = cleaned_views.split("```")[1].replace("json", "").strip()
        views_dict = json.loads(cleaned_views)
    except:
        views_dict = {t: 0.05 for t in tickers}

    # 3. Perform Elite Black-Litterman Optimization
    allocation_dict = PortfolioService.optimize_black_litterman(tickers, views_dict)
    
    # 3. Use LLM to explain the results
    prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/portfolio_prompt.txt")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r") as f:
            base_prompt = f.read()
    else:
        base_prompt = "Act as a portfolio optimizer. Analyze the following tickers: {tickers}"
    
    explanation_prompt = base_prompt.replace("{tickers}", str(tickers))
    explanation_prompt += f"\n\nCalculated Mathematically Optimized Allocation: {json.dumps(allocation_dict)}"
    explanation_prompt += "\n\nPlease explain why this allocation makes sense based on historical volatility and returns."
    
    explanation = call_llm(explanation_prompt, "groq")
    
    # Return both the explanation and the raw data for the UI
    return {
        "portfolio_allocation": explanation,
        "portfolio_data": allocation_dict
    }
