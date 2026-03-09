import os
import json
from llm.llm_router import call_llm
from services.portfolio_service import PortfolioService
from services.market_service import MarketService
from services.factor_engine import FactorEngine
from services.feature_store import FeatureStore

def run_portfolio_agent(state: dict):
    query = state.get("query", "")
    financial_analysis = state.get("financial_analysis", "")
    
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
        return {"portfolio_allocation": "No specific tickers identified for optimization."}

    # 2. Factor Screening & Ranking
    # Fetch historical data and compute factors
    prices = MarketService.get_closing_prices(tickers)
    factors = FactorEngine.compute_all_factors(prices)
    
    # Simple ranking by Sharpe to filter the "Hedge Fund universe"
    ranked_tickers = FactorEngine.rank_assets(factors, primary_factor="sharpe")
    
    # 3. Extract AI "Views" (Expected Returns) from Financial Analysis
    # This turns text into a mathematical prior for Black-Litterman
    view_prompt = f"""
    Based on the following financial analysis and Factor Profile, estimate the expected annual return (as a decimal) for each ticker.
    Analysis: {financial_analysis}
    Factors: {json.dumps(factors)}
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

    # 4. Perform Elite Black-Litterman Optimization
    allocation_dict = PortfolioService.optimize_black_litterman(tickers, views_dict)
    
    # 5. Run Monte Carlo Simulation on the proposed allocation
    monte_carlo_results = PortfolioService.run_monte_carlo(tickers, allocation_dict)
    
    # 6. Use LLM to explain the results
    prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/portfolio_prompt.txt")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r") as f:
            base_prompt = f.read()
    else:
        base_prompt = "Act as a portfolio optimizer. Analyze the following tickers: {tickers}"
    
    explanation_prompt = base_prompt.replace("{tickers}", str(tickers))
    explanation_prompt += f"\n\nCalculated Mathematically Optimized Allocation: {json.dumps(allocation_dict)}"
    explanation_prompt += f"\n\nFactor Screening Profile:\n{json.dumps(factors)}"
    explanation_prompt += f"\n\nMonte Carlo 1-Year Simulation:\n{json.dumps(monte_carlo_results)}"
    explanation_prompt += "\n\nPlease explain why this allocation makes sense based on historical volatility, factor signals, and simulated loss probabilities."
    
    explanation = call_llm(explanation_prompt, "groq")
    
    # Return both the explanation and the raw data for the UI
    return {
        "portfolio_allocation": explanation,
        "portfolio_data": allocation_dict,
        "monte_carlo_results": monte_carlo_results
    }
