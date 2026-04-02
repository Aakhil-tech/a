from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="AgentBridge API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from routes.logs import router as logs_router
from routes.incidents import router as incidents_router
from routes.reports import router as reports_router
from routes.intelligence import router as intelligence_router

app.include_router(logs_router)
app.include_router(incidents_router)
app.include_router(reports_router)
app.include_router(intelligence_router)

@app.get("/")
def root():
    return FileResponse("dashboard.html")

@app.get("/health")
def health():
    return {"status": "AgentBridge API is running", "version": "3.0.0"}
