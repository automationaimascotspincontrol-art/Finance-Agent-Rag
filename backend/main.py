from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.chat import router as chat_router
from api.portfolio import router as portfolio_router

app = FastAPI(title="AI Financial Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(portfolio_router, prefix="/portfolio", tags=["portfolio"])

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Backend is running"}
