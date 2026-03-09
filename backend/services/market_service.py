import yfinance as yf
import pandas as pd
import numpy as np
import os
from typing import List, Optional, Dict
from services.ticker_mapper import TickerMapper

# Global disable for yfinance cache to prevent SQLite locks during reloads
os.environ["YFINANCE_NO_CACHE"] = "1"

class MarketService:
    """
    Handles all market data acquisition, normalization, and preprocessing.
    """
    
    @staticmethod
    def get_closing_prices(tickers: List[str], period: str = "2y") -> pd.DataFrame:
        """
        Fetches closing prices from yfinance with normalization and safety guards.
        """
        try:
            # 1. Normalize tickers (e.g. TCS -> TCS.NS)
            normalized_tickers = TickerMapper.normalize_list(tickers)
            
            # 2. Download without cache/threading to avoid DB locks
            data = yf.download(
                normalized_tickers, 
                period=period, 
                progress=False, 
                threads=False
            )['Close']
            
            if data.empty or (isinstance(data, pd.DataFrame) and data.shape[1] < 1):
                print(f"MarketService: No price data available for {normalized_tickers}")
                return pd.DataFrame()
            
            # Ensure it's a DataFrame even for single ticker
            if isinstance(data, pd.Series):
                data = data.to_frame(name=normalized_tickers[0])
                
            return data
        except Exception as e:
            print(f"MarketService Download Error: {e}")
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
        Calculating quantitative ticker metrics (Beta, Sharpe, Vol).
        """
        normalized_tickers = TickerMapper.normalize_list(tickers)
        all_tickers = normalized_tickers + ["SPY"]
        
        data = MarketService.get_closing_prices(all_tickers)
        if data.empty or "SPY" not in data.columns:
            return {t: {"error": "Insufficient data"} for t in tickers}
            
        returns = MarketService.calculate_log_returns(data)
        if returns.empty:
            return {t: {"error": "Empty returns"} for t in tickers}
            
        spy_returns = returns["SPY"]
        metrics = {}
        
        for ticker in normalized_tickers:
            if ticker not in returns.columns:
                continue
                
            ticker_returns = returns[ticker]
            # Beta Calculation
            covariance = ticker_returns.cov(spy_returns)
            variance = spy_returns.var()
            beta = covariance / variance if variance != 0 else 0
            
            # Sharpe Ratio (3% risk-free rate)
            avg_return = ticker_returns.mean() * 252
            volatility = ticker_returns.std() * (252**0.5)
            sharpe = (avg_return - 0.03) / volatility if volatility != 0 else 0
            
            # Use original ticker in results for UI consistency
            orig_ticker = tickers[normalized_tickers.index(ticker)]
            metrics[orig_ticker] = {
                "beta": round(float(beta), 2),
                "sharpe": round(float(sharpe), 2),
                "volatility": round(float(volatility * 100), 2),
                "return_annual": round(float(avg_return * 100), 2)
            }
            
        return metrics

    @staticmethod
    def get_market_caps(tickers: List[str]) -> Dict[str, float]:
        """
        Fetches market capitalization for the Black-Litterman model.
        """
        caps = {}
        for ticker in tickers:
            norm = TickerMapper.normalize_ticker(ticker)
            try:
                stock = yf.Ticker(norm)
                cap = stock.info.get("marketCap", 1e9) # Default to 1B if missing
                caps[norm] = cap
            except:
                caps[norm] = 1e9
        return caps

    @staticmethod
    def get_stock_fundamentals(ticker: str) -> dict:
        """
        Fetches fundamental data for a single ticker.
        """
        norm = TickerMapper.normalize_ticker(ticker)
        try:
            stock = yf.Ticker(norm)
            info = stock.info
            return {
                "name": info.get("longName"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("forwardPE"),
                "dividend_yield": info.get("dividendYield"),
                "exchange": info.get("exchange")
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_sec_filings_placeholder(ticker: str) -> List[dict]:
        """SEC Filings placeholder."""
        norm = TickerMapper.normalize_ticker(ticker)
        return [
            {"type": "10-K", "date": "2023-12-31", "link": f"https://www.sec.gov/cgi-bin/browse-edgar?CIK={norm}"},
            {"type": "10-Q", "date": "2024-03-31", "link": f"https://www.sec.gov/cgi-bin/browse-edgar?CIK={norm}"}
        ]
