import yfinance as yf
import pandas as pd
import numpy as np
from typing import List, Optional

class MarketService:
    """
    Handles all market data acquisition and preprocessing.
    In the elite version, this would handle caching and polygon.io integration.
    """
    
    @staticmethod
    def get_closing_prices(tickers: List[str], period: str = "2y") -> pd.DataFrame:
        """
        Fetches closing prices from yfinance.
        """
        try:
            data = yf.download(tickers, period=period)['Close']
            if data.empty:
                raise ValueError(f"No data found for tickers {tickers}")
            return data
        except Exception as e:
            print(f"MarketService Error: {e}")
            return pd.DataFrame()

    @staticmethod
    def calculate_log_returns(data: pd.DataFrame) -> pd.DataFrame:
        """
        Computes logarithmic returns for mathematical stability.
        """
        return np.log(data / data.shift(1)).dropna()

    @staticmethod
    def get_ticker_metrics(tickers: List[str]) -> dict:
        """
        Calculating simple ticker metrics for quick analysis.
        """
        all_tickers = tickers + ["SPY"]
        data = MarketService.get_closing_prices(all_tickers)
        if data.empty:
            return {}
            
        returns = MarketService.calculate_log_returns(data)
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
            
            metrics[ticker] = {
                "beta": round(float(beta), 2),
                "sharpe": round(float(sharpe), 2),
                "volatility": round(float(volatility * 100), 2),
                "return_annual": round(float(avg_return * 100), 2)
            }
            
        return metrics

    @staticmethod
    def get_stock_fundamentals(ticker: str) -> dict:
        """
        Fetches fundamental data for a single ticker.
        """
        try:
            stock = yf.Ticker(ticker)
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
            print(f"MarketService Fundamentals Error: {e}")
            return {"error": str(e)}

    @staticmethod
    def get_sec_filings_placeholder(ticker: str) -> List[dict]:
        """
        Provides a placeholder for SEC filings.
        In Elite version, this would use Edgar API or SEC-API.
        """
        return [
            {"type": "10-K", "date": "2023-12-31", "link": f"https://www.sec.gov/cgi-bin/browse-edgar?CIK={ticker}"},
            {"type": "10-Q", "date": "2024-03-31", "link": f"https://www.sec.gov/cgi-bin/browse-edgar?CIK={ticker}"}
        ]
