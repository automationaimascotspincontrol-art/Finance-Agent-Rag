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
    
    # 1. Guardrail: Check for previous errors
    if state.get("quant_error"):
        return {"portfolio_allocation": "Skipped: Mathematical frontier and simulations require valid price data."}

    # 2. Extract and Resolve Tickers Globally
    print("Portfolio: Identifying assets...")
    extraction_prompt = f"Extract company names or stock symbols from: {query}. Return ONLY a JSON list, e.g. ['Tesla', 'TCS', 'Bitcoin']."
    
    try:
        extraction_res = call_llm(extraction_prompt, "groq")
    except Exception as e:
        return {
            "portfolio_allocation": "Error in asset identification.",
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
        print(f"Portfolio Extraction Error: {e}")
        tickers = []

    if not tickers:
        return {"portfolio_allocation": "No specific tickers identified for optimization."}

    # 2. Factor Screening & Ranking
    # Fetch historical data and compute factors
    try:
        prices = MarketService.get_closing_prices(tickers)
        if prices.empty:
            return {"portfolio_allocation": "No price data available for portfolio optimization."}
        
        # Only use tickers with valid price data
        valid_tickers = [t for t in tickers if t in prices.columns and prices[t].dropna().shape[0] >= 30]
        if not valid_tickers:
            return {"portfolio_allocation": "Insufficient price history for portfolio optimization."}
        
        prices = prices[valid_tickers]
        tickers = valid_tickers
        
        factors = FactorEngine.compute_all_factors(prices)
        ranked_tickers = FactorEngine.rank_assets(factors, primary_factor="sharpe")
    except Exception as e:
        print(f"Portfolio: Factor computation error (non-fatal): {e}")
        factors = {}
        ranked_tickers = tickers
    
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
    print("Portfolio: Solving for AI 'Views' vector...")
    try:
        view_res = call_llm(view_prompt, "groq")
        cleaned_views = view_res.strip()
        if "```" in cleaned_views:
            cleaned_views = cleaned_views.split("```")[1].replace("json", "").strip()
        raw_views = json.loads(cleaned_views)
        
        # Strictly constrain views to the valid asset universe to prevent Black-Litterman crashes
        views_dict = {k: v for k, v in raw_views.items() if k in tickers}
        if not views_dict:
            print("Portfolio: LLM generated no valid views for the universe. Defaulting to neutral.")
            views_dict = {t: 0.05 for t in tickers}
            
    except Exception as e:
        print(f"Portfolio View LLM Error: {e}")
        views_dict = {t: 0.05 for t in tickers}

    # 5. Calculate Optimal Weights using Black-Litterman
    print("Portfolio: Solving for AI 'Views' vector...")
    try:
        allocation_dict = PortfolioService.optimize_black_litterman(tickers, views_dict)
    except Exception as e:
        print(f"Portfolio Math Error: {e}")
        allocation_dict = {"error": f"Mathematical optimization failed: {str(e)}"}
    
    # Run Monte Carlo on the weights (only if optimization succeeded)
    monte_carlo_results = {}
    if "error" not in allocation_dict:
        monte_carlo_results = PortfolioService.run_monte_carlo(tickers, allocation_dict)
    else:
        # Provide structural None values so the UI doesn't render "undefined%"
        monte_carlo_results = {
            "expected_return_annual": None,
            "expected_vol_annual": None,
            "prob_loss_next_year": None,
            "var_95_annual": None,
            "error": "Skipped simulation due to optimization failure."
        }
    
    # 6. Use LLM to explain the results
    prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/portfolio_prompt.txt")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r") as f:
            base_prompt = f.read()
    else:
        base_prompt = "Explain optimized allocation: {optimized_weights}"
    
    explanation_prompt = base_prompt.replace("{optimized_weights}", json.dumps(allocation_dict, default=str))
    explanation_prompt = explanation_prompt.replace("{simulation_results}", json.dumps(monte_carlo_results, default=str))
    explanation_prompt = explanation_prompt.replace("{factor_profile}", json.dumps(factors, default=str))
    
    print("Portfolio: Explaining optimized weights and simulations...")
    try:
        explanation = call_llm(explanation_prompt, "groq")
    except Exception as e:
        return {
            "portfolio_allocation": f"Optimization explanation unavailable due to LLM error: {str(e)}",
            "quant_error": True,
            "error_message": f"LLM Failure (Optimization): {str(e)}"
        }
    
    # Return both the explanation and the raw data for the UI
    return {
        "portfolio_allocation": explanation,
        "portfolio_data": allocation_dict,
        "monte_carlo_results": monte_carlo_results
    }
