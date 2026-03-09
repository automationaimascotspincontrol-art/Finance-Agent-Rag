"""
DataPipeline — Institutional-Grade Multi-Source Data Ingestion
==============================================================
Aggregates data from multiple sources into a unified format.
Sources:
  - yfinance: Equities, Crypto, ETFs, Indices (OHLCV + Fundamentals)
  - FRED: Macroeconomic data (Interest Rates, Inflation, GDP, Unemployment)
  - Computed: Technical indicators derived from price data

Philosophy: Data → Mathematics → Signals → Portfolio → Risk
            LLMs never touch this layer.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from functools import lru_cache

# Disable yfinance cache to prevent SQLite locks
os.environ["YFINANCE_NO_CACHE"] = "1"


class DataPipeline:
    """
    Central data ingestion engine.
    All downstream quant modules read from this pipeline.
    """

    # ──────────────────────────────────────────
    # 1. PRICE DATA (OHLCV)
    # ──────────────────────────────────────────

    @staticmethod
    def get_ohlcv(tickers: List[str], period: str = "2y", interval: str = "1d") -> pd.DataFrame:
        """
        Fetches full OHLCV data (Open, High, Low, Close, Volume).
        Returns a MultiIndex DataFrame: (Date) x (Ticker, Field).
        """
        if not tickers:
            return pd.DataFrame()

        try:
            data = yf.download(
                tickers,
                period=period,
                interval=interval,
                progress=False,
                threads=False,
                group_by="ticker"
            )

            if data.empty:
                print(f"DataPipeline: No OHLCV data for {tickers}")
                return pd.DataFrame()

            # For single ticker, yfinance doesn't group by ticker
            if len(tickers) == 1:
                data.columns = pd.MultiIndex.from_product([tickers, data.columns])

            return data

        except Exception as e:
            print(f"DataPipeline OHLCV Error: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_close_prices(tickers: List[str], period: str = "2y") -> pd.DataFrame:
        """
        Extracts just closing prices from OHLCV.
        Backward-compatible with existing MarketService.get_closing_prices.
        """
        if not tickers:
            return pd.DataFrame()

        try:
            data = yf.download(tickers, period=period, progress=False, threads=False)
            if data.empty:
                return pd.DataFrame()

            close = data['Close']
            if isinstance(close, pd.Series):
                close = close.to_frame(name=tickers[0])

            return close.dropna(how='all')

        except Exception as e:
            print(f"DataPipeline Close Error: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_volume(tickers: List[str], period: str = "2y") -> pd.DataFrame:
        """
        Extracts volume data for liquidity analysis.
        """
        if not tickers:
            return pd.DataFrame()

        try:
            data = yf.download(tickers, period=period, progress=False, threads=False)
            if data.empty:
                return pd.DataFrame()

            vol = data['Volume']
            if isinstance(vol, pd.Series):
                vol = vol.to_frame(name=tickers[0])

            return vol.dropna(how='all')

        except Exception as e:
            print(f"DataPipeline Volume Error: {e}")
            return pd.DataFrame()

    # ──────────────────────────────────────────
    # 2. RETURNS (Mathematical Foundation)
    # ──────────────────────────────────────────

    @staticmethod
    def compute_returns(prices: pd.DataFrame, method: str = "log") -> pd.DataFrame:
        """
        Computes returns from price data.
        Methods: 'log' (logarithmic) or 'simple' (arithmetic).
        Log returns are preferred for mathematical stability.
        """
        if prices.empty:
            return pd.DataFrame()

        if method == "log":
            return np.log(prices / prices.shift(1)).dropna()
        else:
            return prices.pct_change().dropna()

    # ──────────────────────────────────────────
    # 3. FUNDAMENTALS (Value Factors)
    # ──────────────────────────────────────────

    @staticmethod
    def get_fundamentals(tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetches fundamental data for value/quality factor computation.
        Returns: {ticker: {pe, pb, ev_ebitda, roe, debt_equity, fcf_yield, ...}}
        """
        fundamentals = {}

        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info

                fundamentals[ticker] = {
                    # Value Factors
                    "pe_ratio": info.get("forwardPE") or info.get("trailingPE"),
                    "pb_ratio": info.get("priceToBook"),
                    "ev_ebitda": info.get("enterpriseToEbitda"),
                    "ps_ratio": info.get("priceToSalesTrailing12Months"),
                    "dividend_yield": info.get("dividendYield"),
                    "fcf_yield": DataPipeline._compute_fcf_yield(info),

                    # Quality Factors
                    "roe": info.get("returnOnEquity"),
                    "roa": info.get("returnOnAssets"),
                    "debt_equity": info.get("debtToEquity"),
                    "current_ratio": info.get("currentRatio"),
                    "gross_margin": info.get("grossMargins"),
                    "operating_margin": info.get("operatingMargins"),
                    "profit_margin": info.get("profitMargins"),
                    "revenue_growth": info.get("revenueGrowth"),
                    "earnings_growth": info.get("earningsGrowth"),

                    # Size & Market
                    "market_cap": info.get("marketCap"),
                    "enterprise_value": info.get("enterpriseValue"),
                    "sector": info.get("sector"),
                    "industry": info.get("industry"),
                    "name": info.get("longName", ticker),

                    # Data Quality
                    "data_quality": "full" if info.get("forwardPE") else "partial"
                }

            except Exception as e:
                print(f"DataPipeline Fundamental Error ({ticker}): {e}")
                fundamentals[ticker] = {"error": str(e), "data_quality": "missing"}

        return fundamentals

    @staticmethod
    def _compute_fcf_yield(info: dict) -> Optional[float]:
        """
        Computes Free Cash Flow Yield = FCF / Market Cap.
        """
        fcf = info.get("freeCashflow")
        mcap = info.get("marketCap")
        if fcf and mcap and mcap > 0:
            return round(fcf / mcap, 4)
        return None

    # ──────────────────────────────────────────
    # 4. MACRO DATA (FRED)
    # ──────────────────────────────────────────

    @staticmethod
    def get_macro_data() -> Dict[str, float]:
        """
        Fetches key macroeconomic indicators.
        Uses yfinance for Treasury yields and VIX as proxies.
        For full FRED integration, requires fredapi library.
        """
        macro = {}

        # Treasury Yields (proxy for risk-free rate and yield curve)
        treasury_tickers = {
            "^TNX": "us_10y_yield",    # 10-Year Treasury Yield
            "^FVX": "us_5y_yield",     # 5-Year Treasury Yield
            "^IRX": "us_3m_yield",     # 3-Month T-Bill
        }

        # Volatility Index
        vix_ticker = "^VIX"

        # Market benchmarks
        benchmark_tickers = {
            "SPY": "sp500_price",
            "QQQ": "nasdaq_price",
            "GLD": "gold_price",
            "TLT": "bond_price",
        }

        all_tickers = list(treasury_tickers.keys()) + [vix_ticker] + list(benchmark_tickers.keys())

        try:
            data = yf.download(all_tickers, period="5d", progress=False, threads=False)
            if data.empty:
                return macro

            close = data["Close"]

            # Treasury Yields
            for ticker, name in treasury_tickers.items():
                if ticker in close.columns:
                    val = close[ticker].dropna()
                    if not val.empty:
                        macro[name] = round(float(val.iloc[-1]), 4)

            # VIX
            if vix_ticker in close.columns:
                vix = close[vix_ticker].dropna()
                if not vix.empty:
                    macro["vix"] = round(float(vix.iloc[-1]), 2)
                    # Regime classification based on VIX
                    vix_val = macro["vix"]
                    if vix_val < 15:
                        macro["volatility_regime"] = "Low (Complacency)"
                    elif vix_val < 25:
                        macro["volatility_regime"] = "Normal"
                    elif vix_val < 35:
                        macro["volatility_regime"] = "Elevated (Fear)"
                    else:
                        macro["volatility_regime"] = "Crisis (Panic)"

            # Benchmarks
            for ticker, name in benchmark_tickers.items():
                if ticker in close.columns:
                    val = close[ticker].dropna()
                    if not val.empty:
                        macro[name] = round(float(val.iloc[-1]), 2)

            # Yield Curve Spread (10Y - 3M): Recession indicator
            if "us_10y_yield" in macro and "us_3m_yield" in macro:
                spread = macro["us_10y_yield"] - macro["us_3m_yield"]
                macro["yield_curve_spread"] = round(spread, 4)
                macro["yield_curve_signal"] = "Inverted (Recession Risk)" if spread < 0 else "Normal"

        except Exception as e:
            print(f"DataPipeline Macro Error: {e}")

        return macro

    # ──────────────────────────────────────────
    # 5. DATA VALIDATION
    # ──────────────────────────────────────────

    @staticmethod
    def validate_prices(prices: pd.DataFrame, min_days: int = 60) -> Dict[str, Any]:
        """
        Validates price data quality.
        Returns a report of data issues.
        """
        report = {
            "total_tickers": len(prices.columns) if not prices.empty else 0,
            "date_range": None,
            "issues": [],
            "valid_tickers": [],
            "invalid_tickers": []
        }

        if prices.empty:
            report["issues"].append("No price data available")
            return report

        report["date_range"] = {
            "start": str(prices.index[0]),
            "end": str(prices.index[-1]),
            "trading_days": len(prices)
        }

        for ticker in prices.columns:
            col = prices[ticker].dropna()

            if len(col) < min_days:
                report["invalid_tickers"].append(ticker)
                report["issues"].append(f"{ticker}: Only {len(col)} days (need {min_days}+)")
            elif col.std() == 0:
                report["invalid_tickers"].append(ticker)
                report["issues"].append(f"{ticker}: Zero variance (stale data)")
            else:
                report["valid_tickers"].append(ticker)

        return report

    @staticmethod
    def validate_fundamentals(fundamentals: Dict[str, Dict]) -> Dict[str, str]:
        """
        Grades the quality of fundamental data per ticker.
        """
        grades = {}
        for ticker, data in fundamentals.items():
            if data.get("error"):
                grades[ticker] = "F (No Data)"
                continue

            core_fields = ["pe_ratio", "roe", "debt_equity", "market_cap"]
            available = sum(1 for f in core_fields if data.get(f) is not None)

            if available == len(core_fields):
                grades[ticker] = "A (Complete)"
            elif available >= 2:
                grades[ticker] = "B (Partial)"
            elif available >= 1:
                grades[ticker] = "C (Sparse)"
            else:
                grades[ticker] = "D (Minimal)"

        return grades

    # ──────────────────────────────────────────
    # 6. UNIFIED PIPELINE ENTRY POINT
    # ──────────────────────────────────────────

    @staticmethod
    def ingest(tickers: List[str], include_fundamentals: bool = True, 
               include_macro: bool = True) -> Dict[str, Any]:
        """
        Master ingestion function.
        Returns a unified data package for downstream quant modules.
        """
        print(f"DataPipeline: Ingesting data for {tickers}...")

        result = {
            "tickers": tickers,
            "timestamp": datetime.now().isoformat(),
            "prices": pd.DataFrame(),
            "volume": pd.DataFrame(),
            "returns_log": pd.DataFrame(),
            "returns_simple": pd.DataFrame(),
            "fundamentals": {},
            "macro": {},
            "validation": {},
            "data_quality_grade": "F"
        }

        # 1. Price Data
        result["prices"] = DataPipeline.get_close_prices(tickers)
        result["volume"] = DataPipeline.get_volume(tickers)

        # 2. Returns
        if not result["prices"].empty:
            result["returns_log"] = DataPipeline.compute_returns(result["prices"], "log")
            result["returns_simple"] = DataPipeline.compute_returns(result["prices"], "simple")

        # 3. Validation
        result["validation"] = DataPipeline.validate_prices(result["prices"])

        # 4. Fundamentals (optional — slower due to per-ticker API calls)
        if include_fundamentals and result["validation"]["valid_tickers"]:
            result["fundamentals"] = DataPipeline.get_fundamentals(
                result["validation"]["valid_tickers"]
            )

        # 5. Macro Data (optional)
        if include_macro:
            result["macro"] = DataPipeline.get_macro_data()

        # 6. Overall Quality Grade
        valid_count = len(result["validation"].get("valid_tickers", []))
        total_count = len(tickers)
        if total_count > 0:
            ratio = valid_count / total_count
            if ratio >= 0.9:
                result["data_quality_grade"] = "A"
            elif ratio >= 0.7:
                result["data_quality_grade"] = "B"
            elif ratio >= 0.5:
                result["data_quality_grade"] = "C"
            else:
                result["data_quality_grade"] = "D"

        print(f"DataPipeline: Complete. Grade={result['data_quality_grade']}, "
              f"Valid={valid_count}/{total_count}, "
              f"Macro={'✓' if result['macro'] else '✗'}")

        return result
