"""
AgentBridge v5 — Decision Gateway
All decisions flow through POST /decide. No bypass possible.
"""
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()

app = FastAPI(
    title="AgentBridge Compliance Gateway",
    version="5.1.0",
    description="Mandatory AI decision enforcement gateway for fintech compliance",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from gateway.security import auth_middleware
app.middleware("http")(auth_middleware)

from routes.gateway_routes import router as gateway_router
from routes.audit_routes import router as audit_router
from routes.intelligence import router as intelligence_router
from routes.manual_log import router as manual_router
from routes.scenarios import router as scenarios_router

app.include_router(gateway_router)
app.include_router(audit_router)
app.include_router(intelligence_router)
app.include_router(manual_router)
app.include_router(scenarios_router)

@app.get("/", include_in_schema=False)
def root():
    dashboard_path = Path(__file__).resolve().parent / "dashboard.html"
    return FileResponse(str(dashboard_path))

@app.get("/health")
def health():
    return {
        "status": "AgentBridge Gateway running",
        "version": "5.1.0",
        "mode": "enforcement",
        "ai_analysis": "groq_enabled" if os.environ.get("GROQ_API_KEY") else "disabled — set GROQ_API_KEY",
        "agent_pipeline": "ready" if os.environ.get("GROQ_API_KEY") else "disabled — set GROQ_API_KEY",
    }

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)
