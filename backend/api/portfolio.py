from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter()

class PortfolioRequest(BaseModel):
    tickers: List[str]

class PortfolioResponse(BaseModel):
    allocation: dict

@router.post("/optimize", response_model=PortfolioResponse)
async def optimize_portfolio(request: PortfolioRequest):
    try:
        from agents.portfolio_agent import optimize_mock
        allocation = optimize_mock(request.tickers)
        return PortfolioResponse(allocation=allocation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
