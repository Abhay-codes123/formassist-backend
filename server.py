from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import sys

# Ensure current directory is always in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()
from config.db import connect_db, close_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()

app = FastAPI(
    title="FormAssist API",
    description="AI-Powered Multilingual Form Assistant Backend",
    version="2.0.0",
    lifespan=lifespan
)

# CORS - Allow all origins (Netlify + local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth Routes
from routes.auth_routes import router as auth_router
app.include_router(auth_router)

# AI Routes
from ai_routes import router as ai_router
app.include_router(ai_router)

@app.get("/")
async def root():
    return {
        "success": True,
        "message": "FormAssist API v2.0 running!",
        "ai": "Gemini powered",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "ok", "service": "FormAssist API", "version": "2.0"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
