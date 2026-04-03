"""
AgentBridge — Report Cleaner v2.0
Transforms raw /report JSON into clean, normalized output for dashboard + PDF export.

Usage:
    python clean_report.py input.json [output.json]
    echo '{...}' | python clean_report.py
    curl .../report?api_key=xxx | python clean_report.py
"""

import json
import sys
import ast
import uuid
from datetime import datetime, timezone


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def parse_raw_field(raw) -> dict:
    """
    Parse input/output fields from Supabase.
    Handles: dict (already parsed), Python-style string, JSON string.
    """
    if isinstance(raw, dict):
        return raw
    if not raw or not isinstance(raw, str) or raw.strip() in ("", "{}", "None", "null"):
        return {}
    try:
        return ast.literal_eval(raw)
    except Exception:
        pass
    try:
        normalized = (
            raw.replace("'", '"')
               .replace("True", "true")
               .replace("False", "false")
               .replace("None", "null")
        )
        return json.loads(normalized)
    except Exception:
        return {"_raw_unparsed": raw}


def gen_decision_id(index: int) -> str:
    short = str(uuid.uuid4())[:8].upper()
    return f"DEC-{short}-{str(index + 1).zfill(3)}"


def fmt_ts(ts) -> str:
    if not ts:
        return "unknown"
    try:
        if isinstance(ts, str):
            # Handle both with and without timezone info
            ts = ts.replace("Z", "+00:00")
            dt = datetime.fromisoformat(ts)
        else:
            dt = ts
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return str(ts)


def compliance_pct(val: str) -> int:
    """'3/5 decisions' → 60"""
    try:
        parts = str(val).replace(" decisions", "").split("/")
        return round(int(parts[0]) / int(parts[1]) * 100)
    except Exception:
        return 0


# ─────────────────────────────────────────
# DECISION CLEANER
# ─────────────────────────────────────────

def clean_decision(raw_dec: dict, index: int) -> dict:
    # Decision ID
    dec_id = raw_dec.get("decision_id")
    if not dec_id or str(dec_id).lower() in ("none", "null", ""):
        dec_id = gen_decision_id(index)
        id_source = "auto_generated"
    else:
        id_source = "original"

    # FIX: handle both dict and string input/output (Supabase stores as string)
    raw_input  = raw_dec.get("input") or raw_dec.get("inputs") or {}
    raw_output = raw_dec.get("output") or {}
    input_data  = parse_raw_field(raw_input)
    output_data = parse_raw_field(raw_output)

    # Reasoning
    reasoning = raw_dec.get("reasoning") or ""
    if not reasoning.strip():
        reasoning = "MISSING — VIOLATION (FREE-AI Clause 3.1)"
        reasoning_valid = False
    else:
        reasoning_valid = True

    # Extract key fields
    amount     = input_data.get("amount")
    kyc        = input_data.get("kyc_verified")
    confidence = output_data.get("confidence") or output_data.get("score")
    action     = raw_dec.get("action_type") or raw_dec.get("action") or "unknown"
    risk       = raw_dec.get("risk_level") or "unknown"

    # Compute flags
    flags = []
    if not reasoning_valid:
        flags.append("missing_reasoning")
    if action == "approve" and kyc is False:
        flags.append("approval_without_kyc")
    if action == "approve" and confidence is not None:
        try:
            if float(confidence) < 0.75:
                flags.append("low_confidence_approval")
        except (TypeError, ValueError):
            pass
    if amount is not None:
        try:
            if float(amount) >= 200000:
                flags.append("critical_value_transaction")
            elif float(amount) >= 50000:
                flags.append("high_value_transaction")
        except (TypeError, ValueError):
            pass
    if raw_dec.get("ai_escalate_to_human"):
        flags.append("escalate_to_human")

    # Parse flag reasons from pipe-separated string
    flag_reasons = [
        f.strip()
        for f in str(raw_dec.get("flag_reason") or "").split("|")
        if f.strip()
    ]

    return {
        "decision_id":        dec_id,
        "decision_id_source": id_source,
        "session_id":         raw_dec.get("session_id") or None,
        "timestamp":          fmt_ts(raw_dec.get("timestamp") or raw_dec.get("created_at")),
        "timestamp_raw":      raw_dec.get("timestamp") or raw_dec.get("created_at") or "",
        "action_type":        action,
        "risk_level":         risk,
        "reasoning":          reasoning,
        "reasoning_valid":    reasoning_valid,
        "input": {
            "amount":       amount,
            "kyc_verified": kyc,
            "raw_parsed":   input_data,
        },
        "output": {
            "confidence":   confidence,
            "raw_parsed":   output_data,
        },
        "computed_flags":     flags,
        "flag_reasons":       flag_reasons,
        # AI analysis fields (populated if Claude/Groq ran)
        "ai_explanation":        raw_dec.get("ai_explanation"),
        "ai_compliance_status":  raw_dec.get("ai_compliance_status"),
        "ai_recommended_action": raw_dec.get("ai_recommended_action"),
        "ai_regulatory_refs":    raw_dec.get("ai_regulatory_refs") or [],
        "ai_escalate_to_human":  raw_dec.get("ai_escalate_to_human", False),
        "ai_confidence_score":   raw_dec.get("ai_confidence_score"),
    }


# ─────────────────────────────────────────
# COMPLIANCE CLEANER
# ─────────────────────────────────────────

def clean_compliance(raw_coverage: dict) -> list:
    result = []
    for clause, val in (raw_coverage or {}).items():
        # Guard: only process "X/Y decisions" format
        if "/" not in str(val):
            continue
        pct = compliance_pct(val)
        result.append({
            "clause":   clause,
            "coverage": val,
            "percent":  pct,
            "status":   "PASS" if pct == 100 else ("PARTIAL" if pct > 0 else "FAIL"),
        })
    return result


def clean_violations(raw_violations: dict) -> list:
    result = []
    for description, count in (raw_violations or {}).items():
        try:
            count = int(count)
        except (TypeError, ValueError):
            count = 1
        result.append({
            "violation":   description,
            "occurrences": count,
            "severity":    "HIGH" if count >= 3 else ("MEDIUM" if count >= 2 else "LOW"),
        })
    return sorted(result, key=lambda x: -x["occurrences"])


# ─────────────────────────────────────────
# MAIN TRANSFORMER
# ─────────────────────────────────────────

def transform(raw: dict) -> dict:
    ss  = raw.get("session_summary") or {}
    rb  = ss.get("risk_breakdown") or {}
    rbi = raw.get("rbi_response_block") or {}

    total    = ss.get("total_decisions") or 0
    flagged  = ss.get("flagged") or 0
    # FIX: use clean count directly — "review" is not clean in gateway v5
    clean_ct = ss.get("clean") or max(0, total - flagged)
    # FIX: score based on truly clean decisions, not (total - flagged)
    score = round((clean_ct / max(total, 1)) * 100)

    raw_decisions   = raw.get("flagged_decisions") or []
    clean_decisions = [clean_decision(d, i) for i, d in enumerate(raw_decisions)]

    # Verdict → machine-readable enum
    verdict_text = raw.get("verdict") or ""
    if "NON-COMPLIANT" in verdict_text or "NON_COMPLIANT" in verdict_text:
        verdict_status = "NON_COMPLIANT"
    elif "PARTIAL" in verdict_text:
        verdict_status = "PARTIAL"
    elif "MOSTLY" in verdict_text:
        verdict_status = "MOSTLY_COMPLIANT"
    elif "COMPLIANT" in verdict_text:
        verdict_status = "COMPLIANT"
    else:
        verdict_status = "UNKNOWN"

    return {
        "_meta": {
            "cleaned_by":       "AgentBridge Report Cleaner v2.0",
            # FIX: use timezone-aware datetime
            "cleaned_at":       datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "source_report_id": raw.get("report_id") or "",
        },
        "report": {
            "report_id":    raw.get("report_id") or "",
            "generated_at": fmt_ts(raw.get("generated_at") or ""),
            "agent_name":   raw.get("agent_name") or "unknown",
            # FIX: use None instead of misleading fallback string
            "session_id":   raw.get("session_id") or None,
        },
        "summary": {
            "total_decisions":   total,
            "flagged_decisions": flagged,
            "clean_decisions":   clean_ct,
            "compliance_score":  f"{score}%",
            "risk_breakdown": {
                "high":   rb.get("high") or 0,
                "medium": rb.get("medium") or 0,
                "low":    rb.get("low") or 0,
            },
        },
        "verdict": {
            "status":          verdict_status,
            "message":         verdict_text,
            "action_required": verdict_status in ("NON_COMPLIANT", "PARTIAL"),
        },
        "decisions": clean_decisions,
        "compliance": {
            "coverage":   clean_compliance(raw.get("compliance_coverage") or {}),
            "violations": clean_violations(raw.get("violation_summary") or {}),
        },
        "rbi_response_block": {
            "prepared_by":             rbi.get("prepared_by") or "AgentBridge Audit System",
            "framework":               rbi.get("framework") or "",
            "session_covered":         rbi.get("session_covered") or "",
            "total_decisions_audited": rbi.get("total_agent_decisions_audited") or total,
            "high_risk_decisions":     rbi.get("high_risk_decisions") or rb.get("high") or 0,
            "compliance_verdict":      rbi.get("compliance_verdict") or verdict_text,
            "generated_at":            fmt_ts(rbi.get("generated_at") or ""),
            "note":                    rbi.get("note") or "",
        },
    }


# ─────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────

def main():
    args = sys.argv[1:]

    if args and args[0] != "-":
        try:
            with open(args[0]) as f:
                raw = json.load(f)
        except FileNotFoundError:
            print(f"Error: file not found: {args[0]}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: invalid JSON in {args[0]}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        try:
            raw = json.load(sys.stdin)
        except json.JSONDecodeError as e:
            print(f"Error: invalid JSON on stdin: {e}", file=sys.stderr)
            sys.exit(1)

    result = transform(raw)
    output = json.dumps(result, indent=2, ensure_ascii=False)

    if len(args) >= 2:
        with open(args[1], "w") as f:
            f.write(output)
        print(f"✓ Cleaned report written to {args[1]}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
