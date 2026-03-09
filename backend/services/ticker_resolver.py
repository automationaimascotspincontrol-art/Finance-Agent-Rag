import yfinance as yf
from typing import List, Optional, Dict

class TickerResolver:
    """
    Fuzzy resolves company names or queries to technical yfinance symbols.
    Works globally (AAPL, TCS.NS, 005930.KS).
    """
    
    @staticmethod
    def resolve(query: str) -> Optional[str]:
        """
        Takes a name like "Tesla" or "TCS" and returns "TSLA" or "TCS.NS".
        """
        try:
            # yfinance search returns metadata about companies
            search = yf.Search(query, max_results=1)
            results = search.quotes
            
            if results and len(results) > 0:
                return results[0]['symbol']
            
            return None
        except Exception as e:
            print(f"TickerResolver Error: {e}")
            # Fallback to simple uppercase
            return query.strip().upper()

    @staticmethod
    def resolve_batch(queries: List[str]) -> List[str]:
        """
        Resolves a list of names/fuzzy strings into symbols.
        """
        symbols = []
        for q in queries:
            s = TickerResolver.resolve(q)
            if s:
                symbols.append(s)
        return list(set(symbols)) # Unique only
