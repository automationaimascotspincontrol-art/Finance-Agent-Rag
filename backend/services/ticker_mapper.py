from typing import List

class TickerMapper:
    """
    Normalizes company tickers for yfinance.
    Appends .NS for Indian stocks (defaulting to NSE) if no suffix exists.
    """
    
    @staticmethod
    def normalize_ticker(ticker: str) -> str:
        ticker = ticker.strip().upper()
        # If it's already got a suffix (e.g. .NS, .BO, .L) leave it
        if "." in ticker:
            return ticker
        
        # Heuristic: Most the user's recent examples (TCS, TATA) are NSE
        # We can expand this with a mapping or query LLM for region
        return f"{ticker}.NS"

    @staticmethod
    def normalize_list(tickers: List[str]) -> List[str]:
        return [TickerMapper.normalize_ticker(t) for t in tickers]
