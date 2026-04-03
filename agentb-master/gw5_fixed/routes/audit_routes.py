"""
routes/audit_routes.py
Audit-specific endpoints: chain verification, incidents, reports.
"""
from fastapi import APIRouter, HTTPException
from database import supabase
from audit_logging.audit_logger import verify_chain
from core_ai.dao import DAO
from core_ai.report_generator import generate_report
import ast

router = APIRouter()


def _parse(raw) -> dict:
    if isinstance(raw, dict):
        return raw
    try:
        return ast.literal_eval(str(raw))
    except Exception:
        return {}


@router.get("/incidents")
async def get_incidents(api_key: str):
    result = supabase.table("audit_logs")\
        .select("*")\
        .eq("api_key", api_key)\
        .eq("flagged", True)\
        .order("created_at", desc=True)\
        .execute()
    return result.data


@router.get("/report")
async def get_report(api_key: str, session_id: str = None):
    query = supabase.table("audit_logs").select("*").eq("api_key", api_key)
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
            agent_name=l.get("agent_id") or "",
            action_type=l.get("action_type") or "unknown",
            risk_level=l.get("risk_level") or "low",
            flag_reason=l.get("policy_violations", [None])[0] if l.get("policy_violations") else None,
            reasoning=l.get("reasoning"),
            compliance_tags=l.get("compliance_tags") or [],
            compliance_violations=l.get("compliance_violations") or [],
            input=_parse(l.get("inputs")),
            output=_parse(l.get("output")),
            ai_explanation=l.get("ai_explanation"),
            ai_recommended_action=l.get("ai_recommended_action"),
            ai_escalate_to_human=l.get("ai_escalate_to_human", False),
            ai_regulatory_refs=l.get("ai_regulatory_refs") or [],
            ai_compliance_status=l.get("ai_compliance_status"),
        )
        daos.append(dao)

    sid = session_id or (logs[0].get("session_id") or "all")
    return generate_report(sid, daos)


@router.get("/verify-chain")
async def verify_audit_chain(api_key: str):
    """
    Verify tamper-evidence of audit log chain.
    Returns {valid: bool, broken_at: decision_id|None, total_checked: int}
    """
    return verify_chain(api_key)
