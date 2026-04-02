"""
AgentBridge SDK
===============
Two lines of code. Full RBI FREE-AI compliance monitoring for any AI agent.

Usage:
    from agentbridge import monitor

    @monitor(api_key="ab_xxxx")
    def your_agent_function(input_data):
        # your existing code unchanged
        return result

    # Or wrap a class method:
    agent = monitor(your_agent_instance, api_key="ab_xxxx")
"""

import time
import uuid
import threading
import traceback
from functools import wraps
from typing import Optional, Any, Dict
from datetime import datetime

try:
    import httpx
    _HTTP_CLIENT = httpx
except ImportError:
    import urllib.request
    import json as _json
    _HTTP_CLIENT = None

# Default backend — overridable
BACKEND_URL = "https://agent-bridge-lh2w.onrender.com"


def _send_log(payload: dict, backend_url: str):
    """Fire and forget — never blocks the agent."""
    def _send():
        try:
            if _HTTP_CLIENT:
                _HTTP_CLIENT.post(
                    f"{backend_url}/log",
                    json=payload,
                    timeout=3
                )
            else:
                data = _json.dumps(payload).encode()
                req = urllib.request.Request(
                    f"{backend_url}/log",
                    data=data,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                urllib.request.urlopen(req, timeout=3)
        except Exception:
            pass  # Never crash the agent

    threading.Thread(target=_send, daemon=True).start()


def monitor(
    func=None,
    *,
    api_key: str = "",
    agent_name: str = "",
    domain: str = "fintech",
    backend_url: str = BACKEND_URL,
    capture_reasoning: bool = True,
):
    """
    Decorator and wrapper for monitoring any AI agent function.

    Args:
        api_key:          Your AgentBridge API key
        agent_name:       Name of this agent (e.g. "FraudDetectorAgent")
        domain:           Industry domain (default: "fintech")
        backend_url:      AgentBridge backend URL
        capture_reasoning: Whether to capture return value as reasoning

    Examples:
        # As decorator
        @monitor(api_key="ab_xxxx", agent_name="FraudAgent")
        def check_fraud(transaction):
            return {"risk": "low"}

        # As wrapper
        monitored_agent = monitor(my_agent_func, api_key="ab_xxxx")
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            start = time.time()
            status = "success"
            output = {}
            error_msg = None
            session_id = str(uuid.uuid4())

            # Capture inputs safely
            try:
                input_data = {}
                if args:
                    input_data["args"] = [str(a)[:200] for a in args]
                if kwargs:
                    input_data["kwargs"] = {
                        k: str(v)[:200] for k, v in kwargs.items()
                    }
            except Exception:
                input_data = {"raw": "could not serialize inputs"}

            try:
                result = f(*args, **kwargs)
                # Capture output
                if isinstance(result, dict):
                    output = result
                else:
                    output = {"result": str(result)[:500]}
                return result

            except Exception as e:
                status = "failed"
                error_msg = str(e)
                output = {"error": error_msg}
                raise

            finally:
                latency = int((time.time() - start) * 1000)
                name = agent_name or f.__name__

                payload = {
                    "api_key": api_key,
                    "agent_name": name,
                    "action": f.__name__,
                    "action_type": _infer_action_type(f.__name__, output),
                    "input": input_data,
                    "output": output,
                    "reasoning": output.get("reasoning") or output.get("explanation") or None,
                    "latency_ms": latency,
                    "status": status,
                    "session_id": session_id,
                    "domain": domain,
                    "timestamp": datetime.utcnow().isoformat(),
                }

                _send_log(payload, backend_url)

        return wrapper

    # Called as @monitor(api_key=...) — return decorator
    if func is None:
        return decorator

    # Called as monitor(func, api_key=...) — wrap immediately
    return decorator(func)


def _infer_action_type(func_name: str, output: dict) -> str:
    """Infer RBI-compatible action type from function name and output."""
    name = func_name.lower()
    out_str = str(output).lower()

    if any(w in name for w in ["approve", "accept", "allow"]):
        return "approve"
    if any(w in name for w in ["reject", "deny", "decline", "block"]):
        return "reject"
    if any(w in name for w in ["flag", "alert", "warn"]):
        return "flag"
    if any(w in name for w in ["escalate", "review", "check"]):
        return "escalate"
    if any(w in name for w in ["query", "fetch", "get", "search"]):
        return "query"

    # Check output for clues
    if "approve" in out_str or "approved" in out_str:
        return "approve"
    if "reject" in out_str or "rejected" in out_str:
        return "reject"
    if "flag" in out_str or "flagged" in out_str:
        return "flag"

    return "unknown"


class AgentBridgeClient:
    """
    Class-based client for more control over monitoring.

    Usage:
        client = AgentBridgeClient(api_key="ab_xxxx", agent_name="MyAgent")

        with client.trace("check_transaction") as trace:
            result = your_logic(data)
            trace.set_output(result)
            trace.set_reasoning("Approved because risk score is below threshold")
    """

    def __init__(
        self,
        api_key: str,
        agent_name: str = "unnamed_agent",
        domain: str = "fintech",
        backend_url: str = BACKEND_URL,
    ):
        self.api_key = api_key
        self.agent_name = agent_name
        self.domain = domain
        self.backend_url = backend_url
        self.session_id = str(uuid.uuid4())

    def log(
        self,
        action: str,
        inputs: Dict = None,
        output: Dict = None,
        reasoning: str = None,
        action_type: str = "unknown",
        latency_ms: int = 0,
        status: str = "success",
    ):
        """Manually log a single agent action."""
        payload = {
            "api_key": self.api_key,
            "agent_name": self.agent_name,
            "action": action,
            "action_type": action_type,
            "input": inputs or {},
            "output": output or {},
            "reasoning": reasoning,
            "latency_ms": latency_ms,
            "status": status,
            "session_id": self.session_id,
            "domain": self.domain,
            "timestamp": datetime.utcnow().isoformat(),
        }
        _send_log(payload, self.backend_url)

    def new_session(self):
        """Start a new session — useful for separating audit periods."""
        self.session_id = str(uuid.uuid4())
        return self.session_id
