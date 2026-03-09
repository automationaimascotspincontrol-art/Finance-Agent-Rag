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
    print("Financial: Identifying assets...")
    extraction_prompt = f"Extract company names or stock symbols from: {query}. Return ONLY a JSON list, e.g. ['Tesla', 'TCS', 'Bitcoin']."
    
    try:
        extraction_res = call_llm(extraction_prompt, "groq")
    except Exception as e:
        return {
            "financial_analysis": "Error in asset identification.",
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
        print(f"Financial Extraction Error: {e}")
        tickers = []

    # 2. Add real fundamentals to prompt
    fundamentals = {}
    macro_data = {}
    if tickers:
        try:
            from services.data_pipeline import DataPipeline
            pipeline_data = DataPipeline.ingest(tickers, include_fundamentals=True, include_macro=True)
            fundamentals = pipeline_data.get("fundamentals", {})
            macro_data = pipeline_data.get("macro", {})
        except Exception as e:
            print(f"Financial: DataPipeline error: {e}")
            fundamentals = {t: "Data unavailable" for t in tickers}
            macro_data = {"error": "Macro data unavailable"}

    # 3. Final prompting
    prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/financial_prompt.txt")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r") as f:
            base_prompt = f.read()
    else:
        base_prompt = "Analyze financial data for {query}."
    
    # The new prompt expects {stock_data}, {macro_data}, and {news} (which comes from research_data)
    prompt = base_prompt.replace("{news}", research_data)
    prompt = prompt.replace("{stock_data}", json.dumps(fundamentals, default=str))
    prompt = prompt.replace("{macro_data}", json.dumps(macro_data, default=str))
    
    print("Financial: Analyzing institutional macro and fundamentals...")
    try:
        analysis = call_llm(prompt, "groq")
    except Exception as e:
        return {
            "financial_analysis": f"Analysis unavailable due to LLM error: {str(e)}",
            "quant_error": True,
            "error_message": f"LLM Failure (Execution): {str(e)}"
        }
    
    return {"financial_analysis": analysis}
