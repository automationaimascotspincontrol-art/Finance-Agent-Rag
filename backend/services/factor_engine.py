import numpy as np
import pandas as pd
from typing import Dict, List

class FactorEngine:
    """
    Computes professional investment signals (factors) from price history.
    Used by Hedge Funds to rank and screen assets.
    """
    
    @staticmethod
    def compute_all_factors(prices: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """
        Computes a suite of factors for a dataframe of closing prices.
        Returns a nested dict: {ticker: {factor_name: value}}
        """
        if prices.empty:
            return {}
            
        returns = prices.pct_change().dropna()
        factors = {}
        
        for ticker in prices.columns:
            ticker_prices = prices[ticker].dropna()
            ticker_returns = returns[ticker].dropna()
            
            if len(ticker_prices) < 20: # Minimum data requirement
                continue
                
            # 1. Momentum (12-month return)
            # 252 trading days in a year
            lookback = min(len(ticker_prices), 252)
            momentum = (ticker_prices.iloc[-1] / ticker_prices.iloc[-lookback]) - 1
            
            # 2. Volatility (Annualized Std Dev)
            volatility = ticker_returns.std() * np.sqrt(252)
            
            # 3. Sharpe Ratio (assumes 3% risk free rate)
            avg_return = ticker_returns.mean() * 252
            sharpe = (avg_return - 0.03) / volatility if volatility != 0 else 0
            
            # 4. Max Drawdown
            cumulative = (1 + ticker_returns).cumprod()
            rolling_max = cumulative.cummax()
            drawdown = (cumulative / rolling_max) - 1
            max_drawdown = drawdown.min()
            
            factors[ticker] = {
                "momentum": round(float(momentum), 4),
                "volatility": round(float(volatility), 4),
                "sharpe": round(float(sharpe), 4),
                "max_drawdown": round(float(max_drawdown), 4),
                "annual_return": round(float(avg_return), 4)
            }
            
        return factors

    @staticmethod
    def rank_assets(factors: Dict[str, Dict[str, float]], primary_factor: str = "sharpe") -> List[str]:
        """
        Ranks assets based on a primary factor (descending).
        """
        sorted_assets = sorted(
            factors.keys(), 
            key=lambda x: factors[x].get(primary_factor, -999), 
            reverse=True
        )
        return sorted_assets
