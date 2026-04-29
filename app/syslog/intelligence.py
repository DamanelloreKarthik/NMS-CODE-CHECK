from collections import defaultdict

def detect_brute_force(logs):
    attempts = defaultdict(int)

    for log in logs:
        if "failed" in log.message.lower():
            key = log.host
            attempts[key] += 1

    attackers = [ip for ip, count in attempts.items() if count > 5]

    return attackers


def detect_unusual_activity(logs):
    night_logs = []

    for log in logs:
        if log.timestamp.hour < 6:
            night_logs.append(log)

    return len(night_logs) > 10