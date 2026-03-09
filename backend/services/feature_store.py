import os
import json
from datetime import datetime
from typing import Dict, List, Optional

class FeatureStore:
    """
    Persists precomputed investment signals (factors) for instant retrieval.
    Enables Bloomberg-level performance by avoiding recomputation.
    """
    
    BASE_DIR = os.path.join(os.path.dirname(__file__), "../storage")
    STORE_FILE = os.path.join(BASE_DIR, "feature_store.json")

    def __init__(self):
        if not os.path.exists(self.BASE_DIR):
            os.makedirs(self.BASE_DIR)
        
        if not os.path.exists(self.STORE_FILE):
            with open(self.STORE_FILE, "w") as f:
                json.dump({}, f)

    def save_features(self, ticker: str, features: Dict[str, float]):
        """
        Updates the store with new factor features for a ticker.
        """
        try:
            with open(self.STORE_FILE, "r") as f:
                store = json.load(f)
            
            store[ticker] = {
                "last_updated": datetime.now().isoformat(),
                "values": features
            }
            
            with open(self.STORE_FILE, "w") as f:
                json.dump(store, f, indent=2)
                
        except Exception as e:
            print(f"FeatureStore Save Error: {e}")

    def get_features(self, ticker: str) -> Optional[Dict[str, float]]:
        """
        Retrieves precomputed features for a ticker if available.
        """
        try:
            with open(self.STORE_FILE, "r") as f:
                store = json.load(f)
                
            entry = store.get(ticker)
            if entry:
                # In a real system, we'd check if the data is stale (e.g. > 1 day)
                return entry.get("values")
            return None
        except:
            return None

    def get_all_features(self) -> Dict[str, Dict]:
        """
        Retrieves the entire store for cross-asset ranking.
        """
        try:
            with open(self.STORE_FILE, "r") as f:
                return json.load(f)
        except:
            return {}

    def get_top_by_factor(self, factor_name: str, limit: int = 5) -> List[str]:
        """
        Returns top tickers ranked by a specific signal (e.g. 'momentum').
        """
        store = self.get_all_features()
        results = []
        for ticker, data in store.items():
            val = data.get("values", {}).get(factor_name)
            if val is not None:
                results.append((ticker, val))
        
        # Sort descending
        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results[:limit]]
