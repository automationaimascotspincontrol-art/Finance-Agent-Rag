import pandas as pd
import numpy as np
import yfinance as yf
from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt import risk_models
from pypfopt import expected_returns
from typing import List, Dict

def get_portfolio_optimization(tickers: List[str]) -> Dict[str, float]:
    """
    Calculates the weights for a Mean-Variance Optimized portfolio.
    Uses real historical data via yfinance.
    """
    try:
        # 1. Fetch historical data for the last 2 years
        data = yf.download(tickers, period="2y")['Close']
        
        # Handle case where column might not exist or data is empty
        if data.empty:
            return {ticker: round(100.0 / len(tickers), 2) for ticker in tickers}

        # 2. Calculate expected returns and sample covariance using Log Returns
        # Log returns are more stable for covariance estimation
        returns = np.log(data / data.shift(1)).dropna()
        mu = expected_returns.mean_historical_return(data) # Ef still expects annual return
        S = risk_models.sample_cov(data, returns=returns)
        
        # 3. Optimize for maximal Sharpe ratio
        ef = EfficientFrontier(mu, S)
        raw_weights = ef.max_sharpe()
        cleaned_weights = ef.clean_weights()
        
        # Convert to percentages and round
        return {ticker: round(weight * 100, 2) for ticker, weight in cleaned_weights.items()}
    except Exception as e:
        print(f"Error in portfolio optimization math: {e}")
        # Return equal weights as fallback if math fails
        return {ticker: round(100.0 / len(tickers), 2) for ticker in tickers}

def get_stock_metrics(tickers: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Calculates Sharpe Ratio, Beta, and Volatility for each stock.
    Beta is calculated relative to SPY (S&P 500).
    """
    try:
        # Fetch tickers + SPY for beta calculation
        all_tickers = tickers + ["SPY"]
        data = yf.download(all_tickers, period="2y")['Close']
        
        # Use log returns for stability
        returns = np.log(data / data.shift(1)).dropna()
        spy_returns = returns["SPY"]
        
        metrics = {}
        for ticker in tickers:
            ticker_returns = returns[ticker]
            
            # Beta Calculation: Cov(r, m) / Var(m)
            covariance = ticker_returns.cov(spy_returns)
            variance = spy_returns.var()
            beta = covariance / variance if variance != 0 else 0
            
            # Sharpe Ratio (Assuming 3% risk-free rate)
            avg_return = ticker_returns.mean() * 252
            volatility = ticker_returns.std() * (252**0.5)
            sharpe = (avg_return - 0.03) / volatility if volatility != 0 else 0
            
            metrics[ticker] = {
                "beta": round(beta, 2),
                "sharpe_ratio": round(sharpe, 2),
                "volatility": round(volatility * 100, 2),  # In percentage
                "annual_return": round(avg_return * 100, 2)
            }
        return metrics
    except Exception as e:
        print(f"Error calculating stock metrics: {e}")
        return {ticker: {"error": str(e)} for ticker in tickers}
