import os
from tavily import TavilyClient
from typing import List, Optional

class NewsService:
    """
    Handles fetching financial news and market sentiments.
    Integrates with Tavily Search API.
    """
    
    def __init__(self):
        api_key = os.getenv("TAVILY_API_KEY")
        self.client = TavilyClient(api_key=api_key) if api_key else None

    def get_market_news(self, query: str, limit: int = 5) -> str:
        """
        Fetches web search results related to financial news.
        """
        if not self.client:
            return "Tavily API Key missing. Skipping news fetch."
            
        try:
            # specialized search context for finance
            search_query = f"Latest financial news and stock analysis for: {query}"
            response = self.client.search(query=search_query, search_depth="advanced", max_results=limit)
            
            results = []
            for result in response.get("results", []):
                results.append(f"Title: {result.get('title')}\nSource: {result.get('url')}\nContent: {result.get('content')}\n")
            
            return "\n".join(results)
            
        except Exception as e:
            print(f"NewsService Error: {e}")
            return f"Error fetching news: {e}"
