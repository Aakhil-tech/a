from datetime import datetime

def check_rules(log: dict) -> tuple[bool, str]:

    # Rule 1 — write operation detected
    write_keywords = ['write', 'update', 'delete', 'create', 'post', 'put', 'patch']
    if any(word in log.get('action', '').lower() for word in write_keywords):
        return True, "Write operation detected — requires compliance review"

    # Rule 2 — outside business hours
    hour = datetime.now().hour
    if hour < 9 or hour > 18:
        return True, f"Action executed outside business hours at {hour}:00"

    # Rule 3 — high latency spike (possible external data leak)
    if log.get('latency_ms', 0) > 5000:
        return True, "Unusually high latency — possible external data exposure"

    return False, ""