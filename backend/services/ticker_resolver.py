import yfinance as yf
from typing import List, Optional, Dict

class TickerResolver:
    """
    Fuzzy resolves company names or queries to technical yfinance symbols.
    Works globally (AAPL, TCS.NS, 005930.KS).
    """
    
    COMMON_MAPPINGS = {
        "BITCOIN": "BTC-USD",
        "BTC": "BTC-USD",
        "ETHEREUM": "ETH-USD",
        "ETH": "ETH-USD",
        "TESLA": "TSLA",
        "NVIDIA": "NVDA",
        "APPLE": "AAPL",
        "MICROSOFT": "MSFT",
        "GOOGLE": "GOOGL",
        "AMAZON": "AMZN",
        "GOLD": "GLD",
        "SILVER": "SLV",
        "TCS": "TCS.NS",
        "RELIANCE": "RELIANCE.NS"
    }
    
    @staticmethod
    def resolve(query: str) -> Optional[str]:
        """
        Takes a name like "Tesla" or "TCS" and returns "TSLA" or "TCS.NS".
        """
        q_upper = query.strip().upper()
        
        # 1. Check Hardcoded Mappings
        if q_upper in TickerResolver.COMMON_MAPPINGS:
            return TickerResolver.COMMON_MAPPINGS[q_upper]

        # 2. Try yfinance Search
        try:
            # yfinance search returns metadata about companies
            search = yf.Search(query, max_results=1)
            results = search.quotes
            
            if results and len(results) > 0:
                symbol = results[0]['symbol']
                # Basic correction for crypto search results if they miss -USD
                if results[0].get('quoteType') == 'CRYPTOCURRENCY' and not symbol.endswith("-USD"):
                    symbol = f"{symbol}-USD"
                return symbol
            
            return q_upper # Fallback to upper case if no results but query is short (e.g. "AAPL")
        except Exception as e:
            print(f"TickerResolver Error: {e}")
            return q_upper

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
