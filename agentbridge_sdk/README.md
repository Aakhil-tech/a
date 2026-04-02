# AgentBridge SDK

RBI FREE-AI compliant monitoring for fintech AI agents.
Two lines of code. Full compliance coverage.

## Install

```bash
pip install agentbridge
```

## Usage — Decorator

```python
from agentbridge import monitor

@monitor(api_key="ab_xxxx", agent_name="FraudDetectorAgent")
def check_transaction_risk(account_id: str, amount: float):
    # your existing code — completely unchanged
    risk_score = your_model.predict(account_id, amount)
    return {
        "risk_score": risk_score,
        "action": "approve" if risk_score < 0.7 else "reject",
        "reasoning": f"Risk score {risk_score} based on transaction history"
    }
```

## Usage — Manual Client

```python
from agentbridge import AgentBridgeClient

client = AgentBridgeClient(api_key="ab_xxxx", agent_name="CreditAgent")

# Log manually with full control
client.log(
    action="credit_decision",
    action_type="approve",
    inputs={"customer_id": "C123", "loan_amount": 50000, "kyc_verified": True},
    output={"approved": True, "limit": 50000},
    reasoning="Customer has clean repayment history and verified KYC",
    latency_ms=142
)
```

## What Gets Monitored

Every call is automatically checked against:
- RBI FREE-AI Framework (August 2025) — 8 compliance clauses
- Anomaly detection — 6 rules including high-value approvals, missing KYC, low confidence
- DPDP Act data protection requirements

## Dashboard

View all your agent actions, incidents, and generate compliance reports at:
https://agentbridge.in (coming soon)
