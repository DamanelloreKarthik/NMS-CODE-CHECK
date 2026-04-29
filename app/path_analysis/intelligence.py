
from typing import List, Dict

def detect_network_anomaly(latency_avg, baseline, packet_loss, route_changed):
    score = 0
    reasons = []


    if baseline and latency_avg:
        deviation = latency_avg / baseline

        if deviation > 1.5:
            score += 2
            reasons.append("HIGH_LATENCY_SPIKE")
        elif deviation > 1.2:
            score += 1
            reasons.append("MODERATE_LATENCY_INCREASE")

    
    if packet_loss:
        if packet_loss > 50:
            score += 2
            reasons.append("CRITICAL_PACKET_LOSS")
        elif packet_loss > 20:
            score += 1
            reasons.append("MODERATE_PACKET_LOSS")

   
    if route_changed:
        score += 1
        reasons.append("ROUTE_CHANGED")

    return {
        "is_anomaly": score >= 2,
        "score": score,
        "reasons": reasons
    }



# NETWORK CLASSIFICATION


def classify_network_issue(hops: List[Dict]):
    if not hops:
        return "UNKNOWN"

    total_hops = len(hops)
    loss_positions = [
        i for i, h in enumerate(hops)
        if h["packet_loss_percent"] == 100
    ]

    if not loss_positions:
        return "STABLE"

    first_loss = loss_positions[0]

    if first_loss == total_hops - 1:
        return "DESTINATION_DOWN"

    if first_loss <= 1:
        return "LAST_MILE_ISSUE"

    if 1 < first_loss < total_hops - 2:
        return "ISP_CONGESTION"

    if len(loss_positions) > total_hops * 0.5:
        return "SEVERE_PACKET_LOSS"

    return "INTERMITTENT_NETWORK_ISSUE"



# PATH STABILITY 


def calculate_path_stability(current_path, history_paths):
    if not history_paths:
        return 100

    total = len(history_paths)
    similarity_scores = []

    curr_ips = [h["ip"] for h in current_path if h["ip"]]

    for past in history_paths:
        past_ips = [h["ip"] for h in past if h["ip"]]

        
        common = set(curr_ips).intersection(set(past_ips))
        union = set(curr_ips).union(set(past_ips))

        if not union:
            similarity = 1
        else:
            similarity = len(common) / len(union)

        similarity_scores.append(similarity)

    avg_similarity = sum(similarity_scores) / total

    
    stability = avg_similarity * 100

    return round(stability, 2)