import os
import re
import json
from llm.llm_router import call_llm
from services.news_service import NewsService

def run_research_agent(state: dict):
    query = state.get("query", "")
    
    # 1. Resolve Tickers for targeted news
    print("Research: Identifying assets for news...")
    extraction_prompt = f"Extract company names or stock symbols from: {query}. Return ONLY a JSON list, e.g. ['Tesla', 'TCS', 'Bitcoin']."
    
    try:
        extraction_res = call_llm(extraction_prompt, "groq")
    except Exception as e:
        return {"research_data": f"Error in asset identification: {str(e)}"}
    
    tickers = []
    try:
        import re
        import json
        match = re.search(r"\[.*\]", extraction_res, re.DOTALL)
        if match:
            cleaned = match.group(0).replace("'", '"')
            queries = json.loads(cleaned)
            from services.market_service import MarketService
            tickers = MarketService.resolve_global_tickers(queries)
        else:
            tickers = []
    except:
        tickers = []

    if not tickers:
        return {"research_data": f"No valid assets found for research. Query: {query}"}

    # 2. Fetch live news for specific tickers
    news_service = NewsService()
    search_query = f"{', '.join(tickers)} latest financial news and market sentiment"
    search_results = news_service.get_market_news(search_query)
    
    # 3. Use LLM to summarize research
    print("Research: Summarizing news sentiment...")
    prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/research_prompt.txt")
    with open(prompt_path, "r") as f:
        prompt = f.read().replace("{query}", query)
    
    full_prompt = f"{prompt}\n\nLive Search Context:\n{search_results}\n\nTickers: {tickers}"
    
    try:
        summary = call_llm(full_prompt, "groq")
    except Exception as e:
        summary = f"Qualitative research unavailable due to LLM error: {str(e)}"
    
    return {"research_data": summary}
