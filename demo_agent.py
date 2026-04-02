"""
AgentBridge Demo Agent
======================
A realistic fake fintech agent that demonstrates AgentBridge monitoring.
Run this and watch your dashboard light up with real compliance data.

Usage:
    python demo_agent.py --api_key ab_xxxx --backend https://your-backend.onrender.com
"""

import time
import random
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from agentbridge_sdk import monitor, AgentBridgeClient

# --- Parse args ---
parser = argparse.ArgumentParser()
parser.add_argument("--api_key", default="demo_key_001")
parser.add_argument("--backend", default="https://agent-bridge-lh2w.onrender.com")
args = parser.parse_args()

client = AgentBridgeClient(
    api_key=args.api_key,
    agent_name="DemoFintechAgent",
    domain="fintech",
    backend_url=args.backend
)

print(f"\n AgentBridge Demo Agent")
print(f" API Key: {args.api_key}")
print(f" Backend: {args.backend}")
print(f" Session: {client.session_id}")
print(f"\n Sending realistic fintech agent actions...\n")

# --- Scenario 1: Normal transaction check ---
def scenario_normal_query():
    client.log(
        action="check_account_balance",
        action_type="query",
        inputs={"account_id": "ACC_" + str(random.randint(1000,9999))},
        output={"balance": random.randint(1000, 100000), "status": "active"},
        reasoning="Routine balance check for transaction processing",
        latency_ms=random.randint(80, 150),
        status="success"
    )
    print("  ✓ Normal query logged")

# --- Scenario 2: Fraud detection with approval ---
def scenario_fraud_approval():
    amount = random.choice([25000, 75000, 150000])
    client.log(
        action="check_transaction_risk",
        action_type="approve",
        inputs={
            "account_id": "ACC_" + str(random.randint(1000,9999)),
            "amount": amount,
            "kyc_verified": True,
            "transaction_type": "transfer"
        },
        output={
            "risk_score": round(random.uniform(0.1, 0.6), 2),
            "approved": True,
            "confidence": round(random.uniform(0.8, 0.99), 2)
        },
        reasoning=f"Transaction of ₹{amount} approved. Risk score within acceptable threshold.",
        latency_ms=random.randint(100, 300),
        status="success"
    )
    print("  ✓ Fraud check (approve) logged")

# --- Scenario 3: HIGH VALUE — will trigger anomaly ---
def scenario_high_value_no_flag():
    client.log(
        action="approve_large_transfer",
        action_type="approve",
        inputs={
            "account_id": "ACC_9999",
            "amount": 250000,  # High value — triggers SUTRA rule
            "kyc_verified": False  # Missing KYC — triggers another rule
        },
        output={
            "approved": True,
            "risk_level": "low"  # Should be high — triggers anomaly
        },
        reasoning=None,  # Missing reasoning — triggers explainability violation
        latency_ms=201,
        status="success"
    )
    print("  ⚠ HIGH VALUE transfer logged — expect incidents in dashboard")

# --- Scenario 4: Rejection ---
def scenario_rejection():
    client.log(
        action="reject_loan_application",
        action_type="reject",
        inputs={
            "customer_id": "CUST_" + str(random.randint(100,999)),
            "loan_amount": random.randint(10000, 500000),
            "credit_score": random.randint(300, 600)
        },
        output={
            "rejected": True,
            "reason": "Credit score below minimum threshold",
            "consecutive_rejections": random.randint(1, 4)
        },
        reasoning="Credit score below minimum threshold of 650 for this loan product",
        latency_ms=random.randint(90, 200),
        status="success"
    )
    print("  ✓ Loan rejection logged")

# --- Scenario 5: KYC verification ---
def scenario_kyc():
    client.log(
        action="verify_customer_kyc",
        action_type="approve",
        inputs={
            "customer_id": "CUST_" + str(random.randint(100,999)),
            "aadhaar_hash": "hash_" + str(random.randint(10000,99999)),
            "kyc_verified": True
        },
        output={
            "kyc_status": "verified",
            "confidence": 0.97
        },
        reasoning="Aadhaar verification successful. Face match confidence 97%.",
        latency_ms=random.randint(200, 800),
        status="success"
    )
    print("  ✓ KYC verification logged")

# --- Run all scenarios ---
scenarios = [
    scenario_normal_query,
    scenario_fraud_approval,
    scenario_kyc,
    scenario_normal_query,
    scenario_fraud_approval,
    scenario_high_value_no_flag,  # This creates incidents
    scenario_rejection,
    scenario_normal_query,
    scenario_kyc,
    scenario_fraud_approval,
]

for i, scenario in enumerate(scenarios):
    scenario()
    time.sleep(0.5)

print(f"\n Demo complete. {len(scenarios)} actions sent.")
print(f" Open your dashboard to see:")
print(f"   - Live action feed with all {len(scenarios)} entries")
print(f"   - 2-3 incidents from the HIGH VALUE scenario")
print(f"   - Compliance score and RBI clause coverage")
print(f"   - Click 'Export Report' to generate your RBI audit document\n")
