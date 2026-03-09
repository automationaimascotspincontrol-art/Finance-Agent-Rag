from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from graph.finance_graph import get_finance_graph

router = APIRouter()

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    response: str

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        graph = get_finance_graph()
        result = graph.invoke({"query": request.query})
        
        return ChatResponse(response=result.get("final_response", "No response generated."))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
