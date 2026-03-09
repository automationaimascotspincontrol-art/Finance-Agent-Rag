from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt import risk_models, expected_returns, black_litterman
import pandas as pd
import numpy as np
from typing import List, Dict
from services.market_service import MarketService

class PortfolioService:
    """
    Handles all portfolio optimization math.
    Decoupled from data fetching via MarketService.
    """
    
    @staticmethod
    def optimize_max_sharpe(tickers: List[str]) -> Dict[str, float]:
        """
        Performs Mean-Variance Optimization for the maximum Sharpe Ratio.
        """
        try:
            # 1. Fetch data via MarketService
            data = MarketService.get_closing_prices(tickers)
            if data.empty:
                return {ticker: round(100.0/len(tickers), 2) for ticker in tickers}
                
            # 2. Compute expected returns and covariance (using log returns stabilization)
            log_returns = MarketService.calculate_log_returns(data)
            mu = expected_returns.mean_historical_return(data)
            S = risk_models.sample_cov(data, returns=log_returns)
            
            # 3. Solve the Efficient Frontier
            ef = EfficientFrontier(mu, S)
            raw_weights = ef.max_sharpe()
            cleaned_weights = ef.clean_weights()
            
            return {ticker: round(weight * 100, 2) for ticker, weight in cleaned_weights.items()}
            
        except Exception as e:
            print(f"PortfolioService Error: {e}")
            return {ticker: round(100.0/len(tickers), 2) for ticker in tickers}

    @staticmethod
    def get_risk_metrics(tickers: List[str]) -> dict:
        """
        Proxies to MarketService to get specialized quantitative metrics.
        """
        return MarketService.get_ticker_metrics(tickers)

    @staticmethod
    def optimize_black_litterman(tickers: List[str], views: Dict[str, float]) -> Dict[str, float]:
        """
        Combines Market Equilibrium with LLM analyst views.
        views: dict mapping ticker to expected annual return (e.g. {"AAPL": 0.15})
        """
        try:
            data = MarketService.get_closing_prices(tickers + ["SPY"])
            if data.empty:
                return {ticker: round(100.0/len(tickers), 2) for ticker in tickers}
            
            # 1. Market Prior (Equilibrium)
            # Use SPY as market proxy for market caps (simplified for this demo)
            # In a real system, we'd use true market caps
            mcaps = {t: 1.0 for t in tickers} 
            S = risk_models.sample_cov(data[tickers])
            
            # 2. Integrate Views
            # Note: PyPortfolioOpt expects views as a series
            view_series = pd.Series(views)
            
            bl = black_litterman.BlackLittermanModel(S, pi="market", absolute_views=view_series)
            ret_bl = bl.bl_returns()
            S_bl = bl.bl_cov()
            
            # 3. Optimize
            ef = EfficientFrontier(ret_bl, S_bl)
            weights = ef.max_sharpe()
            return {ticker: round(weight * 100, 2) for ticker, weight in ef.clean_weights().items()}
        except Exception as e:
            print(f"Black-Litterman Error: {e}")
            return {ticker: round(100.0/len(tickers), 2) for ticker in tickers}
