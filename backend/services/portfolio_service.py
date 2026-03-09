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
                raise ValueError("Insufficient price data for optimization.")
                
            # 2. Compute expected returns and covariance (using log returns stabilization)
            log_returns = MarketService.calculate_log_returns(data)
            mu = expected_returns.mean_historical_return(data)
            S = risk_models.sample_cov(data, returns=log_returns)
            
            # Check for invalid covariance matrix
            if S.isnull().values.any():
                S = risk_models.CustomCovariance().estimate(data) # Fallback to shrinkage if NaNs exist
            
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
            print(f"PortfolioService Max Sharpe Error: {e}")
            raise Exception(f"Optimization failed: {str(e)}")

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
                raise ValueError("Insufficient price data for Black-Litterman optimization.")
            
            # 1. Market Caps (Required for BL Equilibrium)
            caps_dict = MarketService.get_market_caps(tickers)
            market_caps = pd.Series(caps_dict)
            
            # Fill missing market caps with median to prevent NaN blowups on ETFs
            if market_caps.isnull().any():
                market_caps.fillna(market_caps.median(), inplace=True)
                
            # 2. Covariance 
            S = risk_models.sample_cov(data)
            
            # 3. Integrate Views
            norm_views = {TickerMapper.normalize_ticker(t): v for t, v in views.items()}
            # Filter views to only include assets in the data universe
            valid_views = {k: v for k, v in norm_views.items() if k in S.columns}
            if not valid_views:
                raise ValueError("No valid AI views correspond to the price data universe.")
                
            view_series = pd.Series(valid_views)
            
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
            raise Exception(f"Black-Litterman Optimization failed: {str(e)}")

    @staticmethod
    def run_monte_carlo(tickers: List[str], weights: Dict[str, float], num_simulations: int = 10000, days: int = 252) -> Dict[str, any]:
        """
        Runs Monte Carlo simulations to predict future portfolio outcomes.
        """
        try:
            data = MarketService.get_closing_prices(tickers)
            if data.empty:
                return {"error": "No data for simulation"}
                
            returns = data.pct_change().dropna()
            mean_returns = returns.mean()
            cov_matrix = returns.cov()
            
            # Array of weights
            w = np.array([weights.get(t, 0) for t in data.columns]) / 100.0
            
            # Portfolio annual mean and vol
            port_mean = np.sum(mean_returns * w) * days
            port_std = np.sqrt(np.dot(w.T, np.dot(cov_matrix, w))) * np.sqrt(days)
            
            # Simulations (Geometric Brownian Motion)
            sim_returns = np.random.normal(port_mean/days, port_std/np.sqrt(days), (days, num_simulations))
            portfolio_sim = np.cumprod(1 + sim_returns, axis=0)
            
            final_returns = portfolio_sim[-1] - 1
            
            return {
                "expected_return_annual": round(float(port_mean * 100), 2),
                "expected_vol_annual": round(float(port_std * 100), 2),
                "prob_loss_next_year": round(float(np.mean(final_returns < 0) * 100), 2),
                "var_95_annual": round(float(np.percentile(final_returns, 5) * 100), 2),
                "median_simulated_return": round(float(np.median(final_returns) * 100), 2)
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def optimize_min_volatility(tickers: List[str]) -> Dict[str, float]:
        """
        Solves for the portfolio with the minimum possible volatility.
        """
        try:
            data = MarketService.get_closing_prices(tickers)
            if data.empty: return {}
            mu = expected_returns.mean_historical_return(data)
            S = risk_models.sample_cov(data)
            ef = EfficientFrontier(mu, S)
            ef.min_volatility()
            return ef.clean_weights()
        except:
            return {t: round(1/len(tickers), 2) for t in tickers}
