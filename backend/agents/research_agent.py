import os
from llm.llm_router import call_llm
from services.news_service import NewsService

def run_research_agent(state: dict):
    query = state.get("query", "")
    
    # 1. Fetch live news using the new NewsService
    news_service = NewsService()
    search_results = news_service.get_market_news(query)
    
    # 2. Use LLM to summarize research
    prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/research_prompt.txt")
    with open(prompt_path, "r") as f:
        prompt = f.read().replace("{query}", query)
    
    full_prompt = f"{prompt}\n\nLive Search Context:\n{search_results}"
    summary = call_llm(full_prompt, "groq")
    
    return {"research_data": summary}
