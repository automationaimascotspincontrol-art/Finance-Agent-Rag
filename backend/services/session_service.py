import os
import json
from datetime import datetime
from typing import List, Dict, Optional

class SessionService:
    """
    Handles persistence of chat history and user states.
    In the Elite version, this would use SQLAlchemy with PostgreSQL.
    """
    
    BASE_DIR = os.path.join(os.path.dirname(__file__), "../storage")
    HISTORY_FILE = os.path.join(BASE_DIR, "session_history.json")

    def __init__(self):
        if not os.path.exists(self.BASE_DIR):
            os.makedirs(self.BASE_DIR)
        
        if not os.path.exists(self.HISTORY_FILE):
            with open(self.HISTORY_FILE, "w") as f:
                json.dump([], f)

    def save_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Appends a new message to the local storage.
        """
        try:
            with open(self.HISTORY_FILE, "r") as f:
                history = json.load(f)
            
            history.append({
                "timestamp": datetime.now().isoformat(),
                "role": role,
                "content": content,
                "metadata": metadata or {}
            })
            
            # Keep history to last 50 messages to prevent bloat
            history = history[-50:]
            
            with open(self.HISTORY_FILE, "w") as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            print(f"SessionService Error: {e}")

    def get_history(self) -> List[Dict]:
        """
        Retrieves the full chat history.
        """
        try:
            with open(self.HISTORY_FILE, "r") as f:
                return json.load(f)
        except:
            return []

    def clear_history(self):
        """
        Wipes the local history file.
        """
        with open(self.HISTORY_FILE, "w") as f:
            json.dump([], f)
