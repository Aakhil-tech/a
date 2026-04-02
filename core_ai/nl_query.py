"""
Natural language query interface.
Compliance officer asks a question in plain English.
Groq analyzes the actual log data and answers.
"""
import os
import httpx
from typing import List, Dict, Any

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama3-8b-8192"


def query_logs(question: str, logs: List[Dict[str, Any]]) -> str:
    if not GROQ_API_KEY:
        return "GROQ_API_KEY not set."
    if not logs:
        return "No logs found for this API key."

    # Summarize logs into a compact context (avoid token overflow)
    total = len(logs)
    flagged = [l for l in logs if l.get("flagged")]
    high_risk = [l for l in logs if l.get("risk_level") == "high"]
    actions = {}
    for l in logs:
        a = l.get("action", "unknown")
        actions[a] = actions.get(a, 0) + 1

    # Pass last 20 flagged decisions as detail
    sample = flagged[:20] if flagged else logs[:20]
    sample_clean = []
    for l in sample:
        sample_clean.append({
            "action": l.get("action"),
            "action_type": l.get("action_type") or l.get("action"),
            "risk_level": l.get("risk_level"),
            "flag_reason": l.get("flag_reason"),
            "ai_reasoning": l.get("ai_reasoning"),
            "inputs": str(l.get("inputs", ""))[:200],
            "created_at": l.get("created_at"),
        })

    context = f"""You are AgentBridge, a fintech compliance AI.
You have access to real agent decision logs. Answer the compliance officer's question using only this data.

SUMMARY:
- Total decisions: {total}
- Flagged/risky decisions: {len(flagged)}
- High risk decisions: {len(high_risk)}
- Action breakdown: {actions}

FLAGGED DECISION SAMPLES:
{sample_clean}

Be specific, cite decision counts, and reference RBI clauses where relevant.
If you cannot answer from the data, say so clearly."""

    try:
        r = httpx.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": context},
                    {"role": "user", "content": question}
                ],
                "max_tokens": 400,
                "temperature": 0.2,
            },
            timeout=10,
        )
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Query failed: {e}"
