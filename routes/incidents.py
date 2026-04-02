from fastapi import APIRouter, HTTPException
from database import supabase

router = APIRouter()

@router.get("/incidents")
async def get_incidents(api_key: str):
    if not api_key:
        raise HTTPException(status_code=400, detail="api_key required")

    result = supabase.table("logs")\
        .select("*")\
        .eq("api_key", api_key)\
        .eq("flagged", True)\
        .order("created_at", desc=True)\
        .execute()

    return result.data

@router.get("/incidents/{incident_id}")
async def get_incident_detail(incident_id: str, api_key: str):
    result = supabase.table("logs")\
        .select("*")\
        .eq("id", incident_id)\
        .eq("api_key", api_key)\
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Incident not found")

    return result.data[0]