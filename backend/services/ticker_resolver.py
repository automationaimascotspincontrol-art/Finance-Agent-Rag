import yfinance as yf
from typing import List, Optional, Dict

class TickerResolver:
    """
    Fuzzy resolves company names or queries to technical yfinance symbols.
    Works globally (AAPL, TCS.NS, 005930.KS).
    """
    
    COMMON_MAPPINGS = {
        # Crypto
        "BITCOIN": "BTC-USD", "BTC": "BTC-USD", "CRYPTO": "BTC-USD",
        "ETHEREUM": "ETH-USD", "ETH": "ETH-USD",
        "SOLANA": "SOL-USD", "SOL": "SOL-USD",
        "RIPPLE": "XRP-USD", "XRP": "XRP-USD",
        "DOGECOIN": "DOGE-USD", "DOGE": "DOGE-USD",
        
        # Commodities & Asset Classes
        "GOLD": "GLD", "SILVER": "SLV", "OIL": "USO", "CRUDE OIL": "USO",
        "NATURAL GAS": "UNG", "COPPER": "CPER", "PLATINUM": "PPLT",
        
        # Bonds / Fixed Income
        "TREASURY BONDS": "TLT", "TREASURY BOND": "TLT", "TREASURIES": "TLT",
        "T-BONDS": "TLT", "TBONDS": "TLT", "BONDS": "TLT", "BOND": "TLT",
        "US BONDS": "TLT", "US TREASURY": "TLT", "TREASURY": "TLT",
        "SHORT TERM BONDS": "SHY", "TIPS": "TIP",
        
        # Major US Companies
        "TESLA": "TSLA", "NVIDIA": "NVDA", "APPLE": "AAPL",
        "MICROSOFT": "MSFT", "GOOGLE": "GOOGL", "ALPHABET": "GOOGL",
        "AMAZON": "AMZN", "META": "META", "FACEBOOK": "META",
        "NETFLIX": "NFLX", "AMD": "AMD", "INTEL": "INTC",
        "PALANTIR": "PLTR", "COINBASE": "COIN", "SNOWFLAKE": "SNOW",
        
        # Indices / ETFs
        "S&P 500": "SPY", "S&P": "SPY", "SP500": "SPY", "SNP500": "SPY",
        "NASDAQ": "QQQ", "DOW JONES": "DIA", "DOW": "DIA",
        "RUSSELL 2000": "IWM", "EMERGING MARKETS": "EEM",
        "REAL ESTATE": "VNQ", "REIT": "VNQ",
        
        # Indian Stocks
        "TCS": "TCS.NS", "RELIANCE": "RELIANCE.NS", "INFOSYS": "INFY.NS",
        "HDFC": "HDFCBANK.NS", "WIPRO": "WIPRO.NS",
    }
    
    _CACHE = {}

    @staticmethod
    def resolve(query: str) -> Optional[str]:
        """
        Takes a name like "Tesla" or "TCS" and returns "TSLA" or "TCS.NS".
        """
        q_upper = query.strip().upper()
        
        # 1. Check Hardcoded Mappings
        if q_upper in TickerResolver.COMMON_MAPPINGS:
            return TickerResolver.COMMON_MAPPINGS[q_upper]
            
        # 2. Check Cache
        if q_upper in TickerResolver._CACHE:
            return TickerResolver._CACHE[q_upper]

        # 3. Try yfinance Search with timeout safety
        try:
            print(f"TickerResolver: Searching for {query}...")
            search = yf.Search(query, max_results=1)
            results = search.quotes
            
            if results and len(results) > 0:
                symbol = results[0]['symbol']
                # Basic correction for crypto search results if they miss -USD
                if results[0].get('quoteType') == 'CRYPTOCURRENCY' and not symbol.endswith("-USD"):
                    symbol = f"{symbol}-USD"
                
                TickerResolver._CACHE[q_upper] = symbol
                return symbol
            
            return q_upper # Fallback to upper case
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
            if not q: continue
            s = TickerResolver.resolve(q)
            if s:
                symbols.append(s)
        return list(set(symbols)) # Unique only
