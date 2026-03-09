from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt import risk_models, expected_returns, black_litterman
import pandas as pd
import numpy as np
from typing import List, Dict
from services.market_service import MarketService
from services.ticker_mapper import TickerMapper

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
            if data.empty or data.shape[1] < 1:
                return {ticker: round(100.0/len(tickers), 2) for ticker in tickers}
                
            # 2. Compute expected returns and covariance (using log returns stabilization)
            log_returns = MarketService.calculate_log_returns(data)
            mu = expected_returns.mean_historical_return(data)
            S = risk_models.sample_cov(data, returns=log_returns)
            
            # 3. Solve the Efficient Frontier
            ef = EfficientFrontier(mu, S)
            raw_weights = ef.max_sharpe()
            cleaned_weights = ef.clean_weights()
            
            # Use original ticker names in result
            norm_map = {TickerMapper.normalize_ticker(t): t for t in tickers}
            return {
                norm_map.get(ticker, ticker): round(weight * 100, 2) 
                for ticker, weight in cleaned_weights.items()
            }
            
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
            norm_tickers = TickerMapper.normalize_list(tickers)
            data = MarketService.get_closing_prices(tickers) # already normalized inside
            if data.empty:
                return {ticker: round(100.0/len(tickers), 2) for ticker in tickers}
            
            # 1. Market Caps (Required for BL Equilibrium)
            caps_dict = MarketService.get_market_caps(tickers)
            market_caps = pd.Series(caps_dict)
            
            # 2. Covariance 
            S = risk_models.sample_cov(data)
            
            # 3. Integrate Views
            norm_views = {TickerMapper.normalize_ticker(t): v for t, v in views.items()}
            view_series = pd.Series(norm_views)
            
            # Black-Litterman model
            bl = black_litterman.BlackLittermanModel(
                S, 
                pi="market", 
                market_caps=market_caps, 
                absolute_views=view_series
            )
            ret_bl = bl.bl_returns()
            S_bl = bl.bl_cov()
            
            # 4. Optimize
            ef = EfficientFrontier(ret_bl, S_bl)
            weights = ef.max_sharpe()
            cleaned = ef.clean_weights()
            
            # Map back to original tickers
            norm_map = {TickerMapper.normalize_ticker(t): t for t in tickers}
            return {
                norm_map.get(ticker, ticker): round(weight * 100, 2) 
                for ticker, weight in cleaned.items()
            }
        except Exception as e:
            print(f"Black-Litterman Error in PortfolioService: {e}")
            return {ticker: round(100.0/len(tickers), 2) for ticker in tickers}
