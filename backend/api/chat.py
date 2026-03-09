from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from graph.finance_graph import get_finance_graph
from services.session_service import SessionService

router = APIRouter()
session_service = SessionService()

class ChatRequest(BaseModel):
    query: str

async def chat_generator(query: str):
    try:
        # Save user message
        session_service.save_message("user", query)
        
        graph = get_finance_graph()
        # Use astream to get updates as each node completes
        async for event in graph.astream({"query": query}):
            for node_name, output in event.items():
                if node_name == "final":
                    final_content = output.get("final_response")
                    # Save AI final response
                    session_service.save_message("ai", final_content)
                    
                    yield json.dumps({
                        "type": "final", 
                        "content": final_content,
                        "portfolio_data": output.get("portfolio_data"),
                        "quant_data": output.get("quant_data")
                    }) + "\n"
                else:
                    yield json.dumps({
                        "type": "status", 
                        "content": f"{node_name.capitalize()} Agent analysis complete."
                    }) + "\n"
    except Exception as e:
        yield json.dumps({"type": "error", "content": str(e)}) + "\n"

@router.post("/")
async def chat_endpoint(request: ChatRequest):
    return StreamingResponse(chat_generator(request.query), media_type="application/x-ndjson")
