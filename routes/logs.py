from fastapi import APIRouter, HTTPException
from core_ai.pipeline import process
from database import supabase

router = APIRouter()

@router.post("/log")
async def receive_log(data: dict):
    if not data.get("api_key"):
        raise HTTPException(status_code=400, detail="api_key required")
    if not data.get("action") and not data.get("action_type"):
        raise HTTPException(status_code=400, detail="action or action_type required")

    dao = process(data)
    flagged = dao.risk_level in ("high", "medium")

    entry = {
        "api_key": data["api_key"],
        "agent_name": dao.agent_name,
        "action": dao.action_type,
        "inputs": str(dao.input)[:500],
        "output": str(dao.output)[:500],
        "latency_ms": data.get("latency_ms", 0),
        "status": data.get("status", "success"),
        "flagged": flagged,
        "flag_reason": dao.flag_reason,
        "risk_level": dao.risk_level,
        "compliance_tags": dao.compliance_tags,
        "compliance_violations": dao.compliance_violations,
        "reasoning": dao.reasoning,
        "ai_reasoning": dao.ai_reasoning,       # NEW
        "session_id": dao.session_id,
        "decision_id": dao.decision_id,
        "domain": data.get("domain", "fintech"),
    }

    try:
        supabase.table("logs").insert(entry).execute()
    except Exception as e:
        print(f"Warning: Failed to log to Supabase: {e}")

    return {
        "ok": True,
        "decision_id": dao.decision_id,
        "flagged": flagged,
        "risk_level": dao.risk_level,
        "flag_reason": dao.flag_reason,
        "ai_reasoning": dao.ai_reasoning,       # NEW — returned to SDK
        "compliance_tags": dao.compliance_tags,
        "compliance_violations": dao.compliance_violations,
    }

@router.get("/logs")
async def get_logs(api_key: str, limit: int = 50):
    if not api_key:
        raise HTTPException(status_code=400, detail="api_key required")
    result = supabase.table("logs")\
        .select("*")\
        .eq("api_key", api_key)\
        .order("created_at", desc=True)\
        .limit(limit)\
        .execute()
    return result.data
