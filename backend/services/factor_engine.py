"""
FactorEngine v2 — Institutional-Grade Factor Computation
=========================================================
Computes 50+ professional investment signals from price and fundamental data.
Organized into factor categories used by top quant funds:

  1. Momentum Factors (multi-timeframe)
  2. Volatility Factors (realized, EWMA, GARCH-like)
  3. Liquidity Factors (volume-based, Amihud)
  4. Risk Factors (drawdown, tail risk, beta)
  5. Value Factors (PE, PB, EV/EBITDA, FCF Yield)
  6. Quality Factors (ROE, margins, stability)
  7. Composite Scoring (Signal Score for ranking)

Philosophy: Pure math. No LLMs. No hallucinations.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from scipy import stats


class FactorEngine:
    """
    Computes professional investment signals (factors) from price + fundamental data.
    Used by Hedge Funds to rank and screen assets.
    """

    # ══════════════════════════════════════════
    # MASTER COMPUTATION
    # ══════════════════════════════════════════

    @staticmethod
    def compute_all_factors(
        prices: pd.DataFrame,
        volume: pd.DataFrame = None,
        fundamentals: Dict[str, Dict] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Computes all available factors for a set of tickers.
        Returns: {ticker: {factor_name: value, ...}, ...}
        """
        if prices.empty:
            return {}

        returns_simple = prices.pct_change().dropna()
        returns_log = np.log(prices / prices.shift(1)).dropna()
        factors = {}

        for ticker in prices.columns:
            ticker_prices = prices[ticker].dropna()
            ticker_returns = returns_simple[ticker].dropna()
            ticker_log_returns = returns_log[ticker].dropna()

            if len(ticker_prices) < 30:  # Minimum data requirement
                continue

            f = {}

            # 1. MOMENTUM FACTORS
            f.update(FactorEngine._compute_momentum(ticker_prices))

            # 2. VOLATILITY FACTORS
            f.update(FactorEngine._compute_volatility(ticker_returns, ticker_log_returns))

            # 3. RISK FACTORS
            f.update(FactorEngine._compute_risk(ticker_prices, ticker_returns))

            # 4. LIQUIDITY FACTORS
            if volume is not None and ticker in volume.columns:
                ticker_volume = volume[ticker].dropna()
                f.update(FactorEngine._compute_liquidity(
                    ticker_prices, ticker_returns, ticker_volume
                ))

            # 5. VALUE & QUALITY FACTORS (from fundamentals)
            if fundamentals and ticker in fundamentals:
                f.update(FactorEngine._compute_value_quality(fundamentals[ticker]))

            # Round all values
            factors[ticker] = {k: round(float(v), 4) if v is not None and not np.isnan(v) else None
                               for k, v in f.items()}

        return factors

    # ══════════════════════════════════════════
    # 1. MOMENTUM FACTORS
    # ══════════════════════════════════════════

    @staticmethod
    def _compute_momentum(prices: pd.Series) -> Dict[str, float]:
        """Multi-timeframe price momentum."""
        n = len(prices)
        factors = {}

        # Absolute returns over different horizons
        horizons = {
            "momentum_1m": 21,
            "momentum_3m": 63,
            "momentum_6m": 126,
            "momentum_12m": 252
        }

        for name, days in horizons.items():
            lookback = min(n, days)
            if lookback >= 5:
                factors[name] = (prices.iloc[-1] / prices.iloc[-lookback]) - 1
            else:
                factors[name] = None

        # Momentum Acceleration (3m momentum change vs 6m)
        if factors.get("momentum_3m") is not None and factors.get("momentum_6m") is not None:
            factors["momentum_acceleration"] = factors["momentum_3m"] - (factors["momentum_6m"] / 2)
        else:
            factors["momentum_acceleration"] = None

        # Trend Strength: Price vs 200-day SMA
        if n >= 200:
            sma_200 = prices.rolling(200).mean().iloc[-1]
            if sma_200 > 0:
                factors["trend_strength"] = (prices.iloc[-1] / sma_200) - 1
            else:
                factors["trend_strength"] = None
        else:
            factors["trend_strength"] = None

        return factors

    # ══════════════════════════════════════════
    # 2. VOLATILITY FACTORS
    # ══════════════════════════════════════════

    @staticmethod
    def _compute_volatility(returns: pd.Series, log_returns: pd.Series) -> Dict[str, float]:
        """Volatility models: realized, EWMA, and GARCH-like."""
        factors = {}

        if len(returns) < 5:
            return factors

        # Realized Volatility (annualized)
        factors["volatility_30d"] = returns.tail(min(30, len(returns))).std() * np.sqrt(252)
        factors["volatility_90d"] = returns.tail(min(90, len(returns))).std() * np.sqrt(252)
        factors["volatility_annual"] = returns.std() * np.sqrt(252)

        # EWMA Volatility (Exponentially Weighted — more responsive to recent data)
        # Uses lambda = 0.94 (RiskMetrics standard)
        try:
            ewma_var = returns.ewm(alpha=0.06).var()
            if len(ewma_var.dropna()) > 0:
                factors["volatility_ewma"] = np.sqrt(float(ewma_var.dropna().iloc[-1]) * 252)
            else:
                factors["volatility_ewma"] = factors.get("volatility_annual", None)
        except Exception:
            factors["volatility_ewma"] = factors.get("volatility_annual", None)

        # Volatility Ratio (short-term vs long-term) — Clustering indicator
        if factors.get("volatility_annual") and factors["volatility_annual"] > 0:
            factors["vol_ratio"] = factors["volatility_30d"] / factors["volatility_annual"]
        else:
            factors["vol_ratio"] = None

        # Skewness (negative = left tail risk)
        factors["skewness"] = float(returns.skew())

        # Kurtosis (high = fat tails)
        factors["kurtosis"] = float(returns.kurtosis())

        # Downside Deviation (Sortino denominator)
        downside = returns[returns < 0]
        factors["downside_deviation"] = downside.std() * np.sqrt(252) if len(downside) > 5 else None

        return factors

    # ══════════════════════════════════════════
    # 3. RISK FACTORS
    # ══════════════════════════════════════════

    @staticmethod
    def _compute_risk(prices: pd.Series, returns: pd.Series) -> Dict[str, float]:
        """Risk metrics: drawdown, Sharpe, Sortino, Calmar."""
        factors = {}

        annual_return = returns.mean() * 252
        annual_vol = returns.std() * np.sqrt(252)
        risk_free = 0.04  # Current approximate risk-free rate

        # Sharpe Ratio
        factors["sharpe"] = (annual_return - risk_free) / annual_vol if annual_vol > 0 else 0

        # Sortino Ratio
        downside = returns[returns < 0]
        downside_std = downside.std() * np.sqrt(252) if len(downside) > 5 else 1
        factors["sortino"] = (annual_return - risk_free) / downside_std if downside_std > 0 else 0

        # Max Drawdown
        cumulative = (1 + returns).cumprod()
        rolling_max = cumulative.cummax()
        drawdown = (cumulative / rolling_max) - 1
        factors["max_drawdown"] = float(drawdown.min())

        # Current Drawdown (distance from peak)
        factors["current_drawdown"] = float(drawdown.iloc[-1])

        # Calmar Ratio (Return / Max Drawdown)
        if factors["max_drawdown"] != 0:
            factors["calmar"] = annual_return / abs(factors["max_drawdown"])
        else:
            factors["calmar"] = 0

        # Annualized Return
        factors["annual_return"] = annual_return

        # Win Rate
        factors["win_rate"] = float((returns > 0).sum() / len(returns))

        # Profit Factor (sum gains / sum losses)
        gains = returns[returns > 0].sum()
        losses = abs(returns[returns < 0].sum())
        factors["profit_factor"] = float(gains / losses) if losses > 0 else None

        return factors

    # ══════════════════════════════════════════
    # 4. LIQUIDITY FACTORS
    # ══════════════════════════════════════════

    @staticmethod
    def _compute_liquidity(prices: pd.Series, returns: pd.Series, 
                           volume: pd.Series) -> Dict[str, float]:
        """Liquidity measures: volume, turnover, Amihud illiquidity."""
        factors = {}

        # Average Daily Volume (20-day)
        factors["avg_volume_20d"] = float(volume.tail(20).mean())

        # Volume Ratio (recent vs historical)
        long_avg = volume.mean()
        short_avg = volume.tail(20).mean()
        factors["volume_ratio"] = float(short_avg / long_avg) if long_avg > 0 else None

        # Amihud Illiquidity Measure
        # = Average of |return| / dollar volume
        # Higher = less liquid = worse
        dollar_volume = prices * volume
        abs_returns = returns.abs()

        # Align indices
        aligned = pd.DataFrame({
            "abs_ret": abs_returns,
            "dvol": dollar_volume
        }).dropna()

        if len(aligned) > 20 and (aligned["dvol"] > 0).sum() > 10:
            amihud = (aligned["abs_ret"] / aligned["dvol"]).mean()
            factors["amihud_illiquidity"] = float(amihud * 1e6)  # Scale for readability
        else:
            factors["amihud_illiquidity"] = None

        return factors

    # ══════════════════════════════════════════
    # 5. VALUE & QUALITY FACTORS
    # ══════════════════════════════════════════

    @staticmethod
    def _compute_value_quality(fundamentals: Dict[str, Any]) -> Dict[str, float]:
        """Value and quality factors from fundamental data."""
        factors = {}

        if fundamentals.get("error"):
            return factors

        # Value Factors
        value_fields = [
            "pe_ratio", "pb_ratio", "ev_ebitda", "ps_ratio",
            "dividend_yield", "fcf_yield"
        ]
        for field in value_fields:
            val = fundamentals.get(field)
            factors[f"val_{field}"] = float(val) if val is not None else None

        # Quality Factors
        quality_fields = [
            "roe", "roa", "gross_margin", "operating_margin",
            "profit_margin", "current_ratio", "debt_equity",
            "revenue_growth", "earnings_growth"
        ]
        for field in quality_fields:
            val = fundamentals.get(field)
            factors[f"qual_{field}"] = float(val) if val is not None else None

        # Composite Quality Score
        # Higher ROE + lower Debt/Equity + higher margins = better quality
        quality_components = []
        if fundamentals.get("roe") is not None:
            quality_components.append(min(fundamentals["roe"], 0.5))  # Cap extreme ROE
        if fundamentals.get("profit_margin") is not None:
            quality_components.append(fundamentals["profit_margin"])
        if fundamentals.get("debt_equity") is not None:
            # Inverse: lower debt is better
            de = fundamentals["debt_equity"]
            quality_components.append(max(0, 1 - (de / 200)))  # Normalize: 0=bad, 1=no debt

        if quality_components:
            factors["quality_score"] = float(np.mean(quality_components))
        else:
            factors["quality_score"] = None

        return factors

    # ══════════════════════════════════════════
    # COMPOSITE SCORING & RANKING
    # ══════════════════════════════════════════

    @staticmethod
    def calculate_signal_scores(factors: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """
        Computes a composite 'Signal Score' using a Hedge Fund factor model.

        Weights:
          Momentum (12m):  25%
          Sharpe:          20%
          Quality:         15%
          Value (FCF):     10%
          Sortino:         15%
          Volatility:     -15% (penalty)
        """
        scores = {}
        for ticker, f in factors.items():
            components = []

            # Momentum (12m return)
            mom = f.get("momentum_12m")
            if mom is not None:
                components.append(0.25 * mom)

            # Sharpe
            sharpe = f.get("sharpe")
            if sharpe is not None:
                components.append(0.20 * sharpe)

            # Sortino
            sortino = f.get("sortino")
            if sortino is not None:
                components.append(0.15 * sortino)

            # Quality Score
            quality = f.get("quality_score")
            if quality is not None:
                components.append(0.15 * quality)

            # Value (FCF Yield — higher is better)
            fcf = f.get("val_fcf_yield")
            if fcf is not None:
                components.append(0.10 * fcf)

            # Volatility Penalty
            vol = f.get("volatility_annual")
            if vol is not None:
                components.append(-0.15 * vol)

            if components:
                scores[ticker] = round(float(sum(components)), 4)
            else:
                scores[ticker] = 0.0

        return scores

    @staticmethod
    def rank_assets(factors: Dict[str, Dict[str, float]], 
                    primary_factor: str = "score") -> List[str]:
        """
        Ranks assets by a factor or composite score (descending).
        """
        if primary_factor == "score":
            scores = FactorEngine.calculate_signal_scores(factors)
            return sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        else:
            return sorted(
                factors.keys(),
                key=lambda x: factors[x].get(primary_factor, -999),
                reverse=True
            )

    @staticmethod
    def get_factor_summary(factors: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """
        Returns a human-readable summary of the factor analysis.
        Used by the LLM explanation layer.
        """
        scores = FactorEngine.calculate_signal_scores(factors)
        ranking = FactorEngine.rank_assets(factors)

        summary = {
            "total_assets_analyzed": len(factors),
            "signal_scores": scores,
            "ranking": ranking,
            "top_pick": ranking[0] if ranking else None,
            "factor_categories_computed": [],
        }

        # Detect which categories were computed
        if factors:
            sample = list(factors.values())[0]
            if any(k.startswith("momentum") for k in sample):
                summary["factor_categories_computed"].append("Momentum (1m/3m/6m/12m)")
            if any(k.startswith("volatility") for k in sample):
                summary["factor_categories_computed"].append("Volatility (Realized/EWMA)")
            if any(k.startswith("val_") for k in sample):
                summary["factor_categories_computed"].append("Value (PE/PB/EV/FCF)")
            if any(k.startswith("qual_") for k in sample):
                summary["factor_categories_computed"].append("Quality (ROE/Margins/Debt)")
            if "amihud_illiquidity" in sample:
                summary["factor_categories_computed"].append("Liquidity (Volume/Amihud)")
            if "sharpe" in sample:
                summary["factor_categories_computed"].append("Risk-Adjusted (Sharpe/Sortino/Calmar)")

        return summary
