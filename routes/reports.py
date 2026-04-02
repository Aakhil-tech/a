from fastapi import APIRouter, HTTPException
from database import supabase
from core_ai.dao import DAO
from core_ai.report_generator import generate_report
import ast

router = APIRouter()


def _parse_inputs(raw) -> dict:
    if isinstance(raw, dict):
        return raw
    try:
        return ast.literal_eval(str(raw))
    except Exception:
        return {}


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
            decision_id=l.get("decision_id") or "",
            session_id=l.get("session_id") or "",
            timestamp=str(l.get("created_at", "")),
            agent_name=l.get("agent_name") or "",
            action_type=l.get("action") or "unknown",
            risk_level=l.get("risk_level") or "low",
            flag_reason=l.get("flag_reason"),
            reasoning=l.get("reasoning"),
            ai_reasoning=l.get("ai_reasoning"),
            compliance_tags=l.get("compliance_tags") or [],
            compliance_violations=l.get("compliance_violations") or [],
            input=_parse_inputs(l.get("inputs")),
            output=_parse_inputs(l.get("output")),
        )
        daos.append(dao)

    sid = session_id or (logs[0].get("session_id") or "all")
    return generate_report(sid, daos)
