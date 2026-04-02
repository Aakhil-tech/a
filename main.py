from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="AgentBridge API", version="3.0.0")

# CORS — same-origin dashboard works without this,
# but SDK calls from external agents need it open.
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
origins = [o.strip() for o in allowed_origins.split(",") if o.strip()] if allowed_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
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

@app.get("/", include_in_schema=False)
def root():
    return FileResponse("dashboard.html")

@app.get("/health")
def health():
    return {"status": "AgentBridge API is running", "version": "3.0.0"}

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)
