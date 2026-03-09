import json
import time
import traceback
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from graph.finance_graph import get_finance_graph
from services.session_service import SessionService

router = APIRouter()
session_service = SessionService()

class ChatRequest(BaseModel):
    query: str

async def chat_generator(query: str):
    pipeline_start = time.time()
    try:
        # Save user message
        session_service.save_message("user", query)
        
        graph = get_finance_graph()
        print(f"\n{'='*60}")
        print(f"🚀 PIPELINE START: '{query[:80]}...'")
        print(f"{'='*60}")
        
        node_count = 0
        # Use astream to get updates as each node completes
        async for event in graph.astream({"query": query}):
            for node_name, output in event.items():
                node_count += 1
                elapsed = round(time.time() - pipeline_start, 1)
                
                if node_name == "final":
                    final_content = output.get("final_response")
                    print(f"✅ [{elapsed}s] Node #{node_count} '{node_name}' — PIPELINE COMPLETE")
                    print(f"{'='*60}\n")
                    
                    # Save AI final response
                    session_service.save_message("ai", final_content)
                    
                    # Extract raw data for UI visualizations
                    portfolio_data = output.get("portfolio_data", {})
                    quant_data = output.get("quant_data", {})
                    monte_carlo = output.get("monte_carlo_results", {})
                    risk_data = output.get("risk_data", {})
                        
                    yield json.dumps({
                        "type": "final", 
                        "content": final_content,
                        "portfolio_data": portfolio_data,
                        "quant_data": quant_data,
                        "monte_carlo_results": monte_carlo,
                        "risk_data": risk_data
                    }) + "\n"
                else:
                    # Detect errors from agents
                    has_error = output.get("quant_error", False)
                    error_msg = output.get("error_message", "")
                    
                    status_icon = "⚠️" if has_error else "✅"
                    status_detail = f" — ERROR: {error_msg}" if has_error else ""
                    
                    print(f"{status_icon} [{elapsed}s] Node #{node_count} '{node_name}' complete{status_detail}")
                    
                    # Stream detailed status to frontend
                    status_text = f"{node_name.capitalize()} Agent complete."
                    if has_error:
                        status_text = f"{node_name.capitalize()}: {error_msg[:80]}"
                    
                    yield json.dumps({
                        "type": "status", 
                        "content": status_text
                    }) + "\n"
                    
    except Exception as e:
        elapsed = round(time.time() - pipeline_start, 1)
        print(f"\n❌ [{elapsed}s] PIPELINE CRASH:")
        print(traceback.format_exc())
        yield json.dumps({"type": "error", "content": f"Pipeline Error: {str(e)}"}) + "\n"

@router.post("/")
async def chat_endpoint(request: ChatRequest):
    return StreamingResponse(chat_generator(request.query), media_type="application/x-ndjson")

