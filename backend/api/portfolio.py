from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter()

class PortfolioRequest(BaseModel):
    tickers: List[str]

class PortfolioResponse(BaseModel):
    allocation: dict

from services.portfolio_service import PortfolioService

@router.post("/optimize", response_model=PortfolioResponse)
async def optimize_portfolio(request: PortfolioRequest):
    try:
        allocation = PortfolioService.optimize_max_sharpe(request.tickers)
        return PortfolioResponse(allocation=allocation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
