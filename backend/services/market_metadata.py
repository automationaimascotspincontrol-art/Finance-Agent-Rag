import yfinance as yf
from typing import Dict, Optional

class MarketMetadata:
    """
    Classifies assets and detects global currencies for multi-asset portfolios.
    Enables Bloomberg-level asset type detection.
    """
    
    @staticmethod
    def get_metadata(ticker: str) -> Dict[str, str]:
        """
        Returns classification: Equity, ETF, Crypto, Index.
        Also returns currency (USD, INR, KRW, etc).
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Detect asset class
            quote_type = info.get("quoteType", "EQUITY")
            asset_class = "Equity"
            if quote_type == "ETF":
                asset_class = "ETF"
            elif quote_type == "CRYPTOCURRENCY":
                asset_class = "Crypto"
            elif quote_type == "INDEX":
                asset_class = "Index"
            elif ticker.endswith("-USD"): # Backup check for crypto
                asset_class = "Crypto"
                
            return {
                "symbol": ticker,
                "asset_class": asset_class,
                "currency": info.get("currency", "USD"),
                "exchange": info.get("exchange", "Unknown"),
                "quote_type": quote_type
            }
        except Exception:
            # Fallback for failed info fetch
            if ticker.endswith("-USD"):
                return {"symbol": ticker, "asset_class": "Crypto", "currency": "USD"}
            return {"symbol": ticker, "asset_class": "Equity", "currency": "USD"}
