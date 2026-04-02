from fastapi import APIRouter, HTTPException
from database import supabase
from core_ai.dao import DAO
from core_ai.report_generator import generate_report

router = APIRouter()

@router.get("/report")
async def get_report(api_key: str, session_id: str = None):
    if not api_key:
        raise HTTPException(status_code=400, detail="api_key required")

    query = supabase.table("logs").select("*").eq("api_key", api_key)
    if session_id:
        query = query.eq("session_id", session_id)
    logs = query.order("created_at", desc=True).execute().data

    if not logs:
        return {"message": "No data yet for this api_key"}

    daos = []
    for l in logs:
        dao = DAO(
            decision_id=l.get("decision_id", ""),
            session_id=l.get("session_id", ""),
            timestamp=str(l.get("created_at", "")),
            agent_name=l.get("agent_name", ""),
            action_type=l.get("action", "unknown"),
            risk_level=l.get("risk_level", "low"),
            flag_reason=l.get("flag_reason"),
            reasoning=l.get("reasoning"),
            compliance_tags=l.get("compliance_tags", []),
        )
        dao.compliance_violations = l.get("compliance_violations", [])
        daos.append(dao)

    sid = session_id or (logs[0].get("session_id") or "all")
    return generate_report(sid, daos)
