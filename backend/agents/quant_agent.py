"""
Quant Agent v2 — Institutional Math Pipeline
=============================================
This agent is the gateway to the PURE MATH PIPELINE.
It orchestrates: Data Ingestion → Feature Engineering → Scoring → Explanation.

LLMs are used ONLY for:
  1. Ticker extraction from user query
  2. Explaining precomputed math results

LLMs NEVER compute any number.
"""

import os
import re
import json
import time
import traceback
from llm.llm_router import call_llm
from services.data_pipeline import DataPipeline
from services.market_service import MarketService
from services.factor_engine import FactorEngine
from services.feature_store import FeatureStore
from services.portfolio_service import PortfolioService


def run_quant_agent(state: dict):
    query = state.get("query", "")
    t0 = time.time()

    # ───────────────────────────────────────
    # STEP 1: TICKER EXTRACTION (LLM-assisted)
    # ───────────────────────────────────────
    print(f"  [Quant] Step 1: Extracting tickers from query...")
    extraction_prompt = (
        f"Extract company names or stock symbols from: {query}. "
        "Return ONLY a JSON list, e.g. ['Tesla', 'TCS', 'Bitcoin']."
    )

    try:
        extraction_res = call_llm(extraction_prompt, "groq")
    except Exception as e:
        print(f"  [Quant] ❌ LLM extraction failed: {e}")
        return {
            "quant_analysis": "Error in asset extraction.",
            "quant_error": True,
            "error_message": f"LLM Failure (Extraction): {str(e)}"
        }

    print(f"  [Quant] Step 1 done ({round(time.time()-t0, 1)}s). Raw LLM: {extraction_res[:100]}")

    tickers = []
    try:
        match = re.search(r"\[.*\]", extraction_res, re.DOTALL)
        if match:
            cleaned = match.group(0).replace("'", '"')
            queries = json.loads(cleaned)
            tickers = MarketService.resolve_global_tickers(queries)
        else:
            queries = [q.strip() for q in extraction_res.split(",") if q.strip()]
            tickers = MarketService.resolve_global_tickers(queries)
    except Exception as e:
        print(f"  [Quant] ⚠️ Extraction parse error: {e}")
        tickers = []

    print(f"  [Quant] Resolved tickers: {tickers} ({round(time.time()-t0, 1)}s)")

    if not tickers:
        return {
            "quant_analysis": "No assets identified for quantitative analysis.",
            "quant_error": True,
            "error_message": "Ticker resolution failed. No valid symbols found in query."
        }

    # ───────────────────────────────────────
    # STEP 2: DATA INGESTION (Pure Math — No LLM)
    # ───────────────────────────────────────
    t1 = time.time()
    print(f"  [Quant] Step 2: Ingesting data via DataPipeline for {tickers}...")
    try:
        pipeline_data = DataPipeline.ingest(tickers, include_fundamentals=True, include_macro=True)
    except Exception as e:
        print(f"  [Quant] ❌ DataPipeline crashed: {e}")
        traceback.print_exc()
        return {
            "quant_analysis": "Data pipeline error.",
            "quant_error": True,
            "error_message": f"DataPipeline Error: {str(e)}"
        }

    print(f"  [Quant] Step 2 done ({round(time.time()-t1, 1)}s). Quality: {pipeline_data['data_quality_grade']}")

    if pipeline_data["prices"].empty:
        return {
            "quant_analysis": "Quantitative analysis unavailable due to missing price data.",
            "quant_error": True,
            "error_message": f"Market data fetch failed for {tickers}."
        }

    # Validate data quality
    validation = pipeline_data["validation"]
    valid_tickers = validation.get("valid_tickers", [])
    if not valid_tickers:
        return {
            "quant_analysis": "Insufficient data quality for analysis.",
            "quant_error": True,
            "error_message": f"Data validation failed: {validation.get('issues', [])}"
        }

    # ───────────────────────────────────────
    # STEP 3: FACTOR COMPUTATION (Pure Math — No LLM)
    # ───────────────────────────────────────
    t2 = time.time()
    print(f"  [Quant] Step 3: Computing 50+ factors for {valid_tickers}...")
    try:
        # Safely select columns that exist in the dataframe
        price_cols = [t for t in valid_tickers if t in pipeline_data["prices"].columns]
        vol_cols = [t for t in valid_tickers if not pipeline_data["volume"].empty and t in pipeline_data["volume"].columns]
        
        factors_dict = FactorEngine.compute_all_factors(
            prices=pipeline_data["prices"][price_cols] if price_cols else pipeline_data["prices"],
            volume=pipeline_data["volume"][vol_cols] if vol_cols else None,
            fundamentals=pipeline_data.get("fundamentals", {})
        )
    except Exception as e:
        print(f"  [Quant] ❌ FactorEngine crashed: {e}")
        traceback.print_exc()
        return {
            "quant_analysis": "Factor computation error.",
            "quant_error": True,
            "error_message": f"FactorEngine Error: {str(e)}"
        }

    print(f"  [Quant] Step 3 done ({round(time.time()-t2, 1)}s). Factors for {list(factors_dict.keys())}")

    # Risk metrics from portfolio service
    try:
        metrics_dict = PortfolioService.get_risk_metrics(valid_tickers)
    except Exception as e:
        print(f"  [Quant] ⚠️ Risk metrics error (non-fatal): {e}")
        metrics_dict = {}

    # Signal Scores & Ranking
    scores = FactorEngine.calculate_signal_scores(factors_dict)
    factor_summary = FactorEngine.get_factor_summary(factors_dict)
    print(f"  [Quant] Signal Scores: {scores}")
    print(f"  [Quant] Ranking: {factor_summary['ranking']}")

    # ───────────────────────────────────────
    # STEP 4: PERSIST TO FEATURE STORE
    # ───────────────────────────────────────
    try:
        feature_store = FeatureStore()
        for t, fs in factors_dict.items():
            feature_store.save_features(t, fs)
    except Exception as e:
        print(f"  [Quant] ⚠️ Feature store save error (non-fatal): {e}")

    # ───────────────────────────────────────
    # STEP 5: LLM EXPLANATION (Interpret precomputed results)
    # ───────────────────────────────────────
    t3 = time.time()
    print(f"  [Quant] Step 5: Generating LLM explanation...")
    prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/quant_prompt.txt")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r") as f:
            base_prompt = f.read()
    else:
        base_prompt = "Analyze these precomputed metrics: {quant_data}"

    # Build the explanation prompt with ALL computed data
    explanation_data = {
        "factors": factors_dict,
        "signal_scores": scores,
        "ranking": factor_summary["ranking"],
        "top_pick": factor_summary["top_pick"],
        "factor_categories": factor_summary["factor_categories_computed"],
        "macro_environment": pipeline_data.get("macro", {}),
        "data_quality": pipeline_data["data_quality_grade"],
    }

    analysis_prompt = base_prompt.replace("{quant_data}", json.dumps(explanation_data, default=str))
    analysis_prompt += f"\n\nPrecomputed Risk Metrics:\n{json.dumps(metrics_dict, default=str)}"
    analysis_prompt += "\n\nIMPORTANT: Report the EXACT numbers shown above. Do NOT invent any numbers."

    try:
        analysis = call_llm(analysis_prompt, "groq")
    except Exception as e:
        print(f"  [Quant] ❌ LLM explanation failed: {e}")
        return {
            "quant_analysis": "Error explaining quantitative metrics.",
            "quant_error": True,
            "error_message": f"LLM Failure (Analysis): {str(e)}"
        }

    print(f"  [Quant] Step 5 done ({round(time.time()-t3, 1)}s)")
    print(f"  [Quant] ✅ TOTAL TIME: {round(time.time()-t0, 1)}s")

    # ───────────────────────────────────────
    # STEP 6: RETURN RESULTS
    # ───────────────────────────────────────
    return {
        "quant_analysis": analysis,
        "quant_data": {
            **metrics_dict,
            **factors_dict,
            "signal_scores": scores,
            "ranking": factor_summary["ranking"],
            "macro": pipeline_data.get("macro", {}),
            "data_quality": pipeline_data["data_quality_grade"],
            "factor_categories": factor_summary["factor_categories_computed"]
        },
        "quant_error": False
    }

