import numpy as np
import pandas as pd
from typing import Dict, List, Optional

class RiskEngine:
    """
    Handles institutional-grade risk modeling.
    Calculates VaR, CVaR, Tail Risk, and Correlation Matrices.
    """
    
    @staticmethod
    def calculate_var_cvar(returns: pd.DataFrame, confidence_level: float = 0.95) -> Dict[str, Dict[str, float]]:
        """
        Calculates Value at Risk (VaR) and Conditional Value at Risk (CVaR).
        Meaning: 5% (if 0.95) worst-case daily loss.
        """
        if returns.empty:
            return {}
            
        results = {}
        for ticker in returns.columns:
            ticker_returns = returns[ticker].dropna()
            if ticker_returns.empty:
                continue
                
            # VaR (Historical)
            var = np.percentile(ticker_returns, (1 - confidence_level) * 100)
            
            # CVaR (Expected Shortfall)
            cvar = ticker_returns[ticker_returns <= var].mean()
            
            results[ticker] = {
                "var_95": round(float(var), 4),
                "cvar_95": round(float(cvar), 4)
            }
            
        return results

    @staticmethod
    def get_correlation_matrix(returns: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """
        Returns a JSON-serializable correlation matrix.
        """
        if returns.empty:
            return {}
        corr = returns.corr()
        return corr.to_dict()

    @staticmethod
    def analyze_tail_risk(returns: pd.DataFrame) -> Dict[str, str]:
        """
        Heuristic-based tail risk analysis.
        """
        risk_levels = {}
        for ticker in returns.columns:
            # Skewness and Kurtosis for tail-risk detection
            skew = returns[ticker].skew()
            kurt = returns[ticker].kurtosis()
            
            level = "Normal"
            if skew < -1 or kurt > 3:
                level = "High (Fat Tails)"
            elif skew < -0.5 or kurt > 1:
                level = "Moderate"
                
            risk_levels[ticker] = level
            
        return risk_levels
