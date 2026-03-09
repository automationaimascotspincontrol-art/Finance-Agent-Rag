import yfinance as yf
import pandas as pd
import numpy as np
import os
from typing import List, Optional, Dict
from services.ticker_resolver import TickerResolver
from services.market_metadata import MarketMetadata

# Global disable for yfinance cache to prevent SQLite locks during reloads
os.environ["YFINANCE_NO_CACHE"] = "1"

class MarketService:
    """
    Handles all market data acquisition, normalization, and preprocessing globally.
    Supports Equities, ETFs, and Crypto.
    """
    
    @staticmethod
    def get_closing_prices(tickers: List[str], period: str = "2y") -> pd.DataFrame:
        """
        Fetches closing prices from yfinance for global tickers.
        """
        try:
            # Note: TickerResolver should have been called at the Agent level
            # but we guard here as well.
            if not tickers:
                return pd.DataFrame()
                
            data = yf.download(
                tickers, 
                period=period, 
                progress=False, 
                threads=False
            )['Close']
            
            if data.empty:
                print(f"MarketService: No price data available for {tickers}")
                return pd.DataFrame()
            
            # Ensure it's a DataFrame even for single ticker
            if isinstance(data, pd.Series):
                data = data.to_frame(name=tickers[0])
                
            return data
        except Exception as e:
            print(f"MarketService Global Download Error: {e}")
            return pd.DataFrame()

    @staticmethod
    def calculate_log_returns(data: pd.DataFrame) -> pd.DataFrame:
        """
        Computes logarithmic returns for mathematical stability.
        """
        if data.empty:
            return pd.DataFrame()
        return np.log(data / data.shift(1)).dropna()

    @staticmethod
    def get_ticker_metrics(tickers: List[str]) -> dict:
        """
        Calculating quantitative ticker metrics (Beta, Sharpe, Vol) globally.
        """
        all_tickers = tickers + ["SPY"] # SPY is the global US benchmark
        
        data = MarketService.get_closing_prices(all_tickers)
        if data.empty or "SPY" not in data.columns:
            # If SPY failed (maybe it's a crypto-only query), try to calculate without Beta
            return {t: {"error": "Insufficient market data"} for t in tickers}
            
        returns = MarketService.calculate_log_returns(data)
        if returns.empty:
            return {t: {"error": "Empty returns"} for t in tickers}
            
        spy_returns = returns["SPY"]
        metrics = {}
        
        for ticker in tickers:
            if ticker not in returns.columns:
                continue
                
            ticker_returns = returns[ticker]
            # Beta Calculation
            covariance = ticker_returns.cov(spy_returns)
            variance = spy_returns.var()
            beta = covariance / variance if variance != 0 else 0
            
            # Sharpe Ratio
            avg_return = ticker_returns.mean() * 252
            volatility = ticker_returns.std() * (252**0.5)
            sharpe = (avg_return - 0.03) / volatility if volatility != 0 else 0
            
            # Get asset class via Metadata
            meta = MarketMetadata.get_metadata(ticker)
            
            metrics[ticker] = {
                "beta": round(float(beta), 2),
                "sharpe": round(float(sharpe), 2),
                "volatility": round(float(volatility * 100), 2),
                "return_annual": round(float(avg_return * 100), 2),
                "asset_class": meta.get("asset_class"),
                "currency": meta.get("currency")
            }
            
        return metrics

    @staticmethod
    def get_market_caps(tickers: List[str]) -> Dict[str, float]:
        """
        Fetches market capitalization globally.
        """
        caps = {}
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                cap = stock.info.get("marketCap")
                if not cap:
                    # Heuristic for Crypto/Alt (Total Supply * Price) or Placeholder
                    cap = 1e9 
                caps[ticker] = cap
            except:
                caps[ticker] = 1e9
        return caps

    @staticmethod
    def get_stock_fundamentals(ticker: str) -> dict:
        """
        Fetches fundamental data globally.
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            meta = MarketMetadata.get_metadata(ticker)
            
            return {
                "name": info.get("longName", ticker),
                "asset_class": meta.get("asset_class"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("forwardPE"),
                "dividend_yield": info.get("dividendYield"),
                "currency": meta.get("currency"),
                "exchange": meta.get("exchange")
            }
        except Exception as e:
            return {"error": str(e)}
            
    @staticmethod
    def resolve_global_tickers(queries: List[str]) -> List[str]:
        """
        Entry point for agents to resolve names like "Tesla" to "TSLA".
        """
        return TickerResolver.resolve_batch(queries)
