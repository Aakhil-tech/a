from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

@dataclass
class DAO:
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    input: Dict[str, Any] = field(default_factory=dict)
    reasoning: Optional[str] = None
    ai_reasoning: Optional[str] = None        # NEW: Groq-generated reasoning
    output: Dict[str, Any] = field(default_factory=dict)

    risk_level: str = "low"
    flag_reason: Optional[str] = None

    compliance_tags: List[str] = field(default_factory=list)
    compliance_violations: List[str] = field(default_factory=list)  # FIXED: now proper field

    agent_name: str = ""
    action_type: str = ""

    def to_dict(self):
        return {
            "decision_id": self.decision_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "input": self.input,
            "reasoning": self.reasoning,
            "ai_reasoning": self.ai_reasoning,
            "output": self.output,
            "risk_level": self.risk_level,
            "flag_reason": self.flag_reason,
            "compliance_tags": self.compliance_tags,
            "compliance_violations": self.compliance_violations,
            "agent_name": self.agent_name,
            "action_type": self.action_type,
        }
