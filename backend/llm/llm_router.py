from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import time
import os
from dotenv import load_dotenv

load_dotenv()

# Tier 1: High-reasoning model (Groq 70B)
llm_70b = ChatGroq(
    temperature=0,
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

# Tier 2: Fast/Resilient model (Groq 8B)
llm_8b = ChatGroq(
    temperature=0,
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY")
)

# Tier 3: Local "Infinite Fallback" (Ollama / LM Studio)
local_url = os.getenv("LOCAL_LLM_URL", "http://localhost:11434/v1")
local_model = os.getenv("LOCAL_LLM_MODEL", "llama3")
llm_local = ChatOpenAI(
    base_url=local_url,
    api_key="none", # Local endpoints usually don't need this
    model=local_model,
    temperature=0
)

def call_llm(prompt: str, model_type="groq", use_fallback=True):
    """
    Calls LLM with three-tier resilience: 70b -> 8b -> Local.
    """
    # 1. Primary Attempt (70b)
    try:
        response = llm_70b.invoke([HumanMessage(content=prompt)])
        return response.content
    except Exception as e:
        if not use_fallback:
            raise Exception(f"LLM API Error (70b): {str(e)}")
            
        # 2. Secondary Attempt (8b)
        print(f"llm_router: Primary 70b failed ({str(e)[:50]}). Falling back to 8b...")
        try:
            response = llm_8b.invoke([HumanMessage(content=prompt)])
            return response.content
        except Exception as e8:
            # 3. Tertiary Attempt (Local)
            print(f"llm_router: Secondary 8b failed ({str(e8)[:50]}). Falling back to LOCAL model...")
            try:
                response = llm_local.invoke([HumanMessage(content=prompt)])
                return response.content
            except Exception as el:
                raise Exception(f"CRITICAL: All three LLM tiers failed. (Local error: {str(el)})")
