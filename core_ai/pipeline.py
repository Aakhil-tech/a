from core_ai.dao import DAO
from core_ai.parser import parse_to_dao
from core_ai.anomaly import check_anomalies
from core_ai.compliance import map_compliance
from core_ai.groq_reasoning import generate_reasoning
from typing import Any, Dict


def process(raw_log: Dict[str, Any]) -> DAO:
    # Step 1: Parse
    dao = parse_to_dao(raw_log)

    # Step 2: Anomaly check
    dao = check_anomalies(dao)

    # Step 3: Compliance mapping
    dao = map_compliance(dao)

    # Step 4: Generate AI reasoning if missing and flagged
    if (not dao.reasoning or dao.reasoning.strip() == "") and dao.risk_level in ("high", "medium"):
        dao.ai_reasoning = generate_reasoning(dao)

    return dao
