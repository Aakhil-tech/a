import os
import httpx

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama3-8b-8192"  # Fast + free tier


def generate_reasoning(dao) -> str:
    """
    Calls Groq to generate a compliance reasoning explanation
    for a flagged decision. Only called when agent provided no reasoning.
    """
    if not GROQ_API_KEY:
        return "AI reasoning unavailable — GROQ_API_KEY not set."

    prompt = f"""You are a fintech compliance analyst reviewing an AI agent decision.

Agent: {dao.agent_name}
Action: {dao.action_type}
Input: {dao.input}
Output: {dao.output}
Risk Level: {dao.risk_level}
Flags: {dao.flag_reason}

The agent provided no reasoning. In 2-3 sentences, explain what likely happened and why this decision is risky from an RBI compliance perspective."""

    try:
        r = httpx.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 150,
                "temperature": 0.3,
            },
            timeout=8,
        )
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"AI reasoning generation failed: {e}"
