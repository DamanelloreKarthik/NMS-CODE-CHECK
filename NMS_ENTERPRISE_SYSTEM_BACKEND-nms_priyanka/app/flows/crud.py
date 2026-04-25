
from sqlalchemy import func
from app.flows.models import NetFlowRecord
from collections import defaultdict
from app.flows.services import (
    base_query, apply_explorer_filters, get_flow_overview,
    get_top_talkers, get_pattern_recognition, get_intelligent_insights,
    get_timeline, get_performance_trends, get_latency_distribution,
    detect_anomalies, get_flow_direction, get_flow_status,
    classify_protocol, enrich_application, get_protocol_name,
    format_bytes, format_bytes_struct,
)


# -------------------------
# REAL TIME ANALYTICS
# -------------------------

def get_real_time(db, start_time, end_time, event_source=None, interface=None):
    q = base_query(db, start_time, end_time, event_source, interface)

    total_flows = q.count()
    total_bytes = q.with_entities(func.sum(NetFlowRecord.bytes)).scalar() or 0

    seconds = max((end_time - start_time).total_seconds(), 1)

    # ✅ convert bytes properly
    if total_bytes < 1024:
        value, unit = total_bytes, "B"
    elif total_bytes < 1024**2:
        value, unit = round(total_bytes / 1024, 2), "KB"
    elif total_bytes < 1024**3:
        value, unit = round(total_bytes / (1024**2), 2), "MB"
    else:
        value, unit = round(total_bytes / (1024**3), 2), "GB"

    return {
        "events_per_sec": round(total_flows / seconds, 2),
        "flow_events": total_flows,
        "flow_volume": {
            "value": value,
            "unit": unit
        }
    }

# -------------------------
# PROTOCOL DISTRIBUTION
# -------------------------
def get_protocol_distribution(db, start_time, end_time, event_source=None, interface=None, limit=5):
    q = base_query(db, start_time, end_time, event_source, interface).all()

    stats = {}

    for r in q:
        proto = classify_protocol(r.protocol, r.src_port, r.dst_port)

        if proto not in stats:
            stats[proto] = {"bytes": 0, "flows": 0}

        stats[proto]["bytes"] += r.bytes
        stats[proto]["flows"] += 1

    total_bytes = sum(v["bytes"] for v in stats.values()) or 1

    sorted_items = sorted(stats.items(), key=lambda x: x[1]["bytes"], reverse=True)

    top = sorted_items[:limit]
    others = sorted_items[limit:]

    merged = {}
    flows_map = {}
    other_bytes = 0
    other_flows = 0

    for name, data in top:
        if name == "OTHER":
            other_bytes += data["bytes"]
            other_flows += data["flows"]
        else:
            merged[name] = data["bytes"]
            flows_map[name] = data["flows"]

    for name, data in others:
        other_bytes += data["bytes"]
        other_flows += data["flows"]

    if other_bytes > 0:
        merged["OTHER"] = other_bytes
        flows_map["OTHER"] = other_flows

    return [
        {
            "protocol": name,
            "bytes": val,
            "bytes_formatted": format_bytes(val),
            "flows": flows_map[name],
            "percentage": round((val / total_bytes) * 100, 2)
        }
        for name, val in merged.items()
    ]


# -------------------------
# TRAFFIC DISTRIBUTION
# -------------------------
def get_traffic_distribution(db, start_time, end_time, event_source=None, interface=None):
    q = base_query(db, start_time, end_time, event_source, interface).all()

    app_stats = {}
    proto_stats = {}

    # -------------------------
    # COLLECT STATS
    # -------------------------
    for r in q:
        # L7 (Application)
        app = classify_protocol(r.protocol, r.src_port, r.dst_port)
        app_stats[app] = app_stats.get(app, 0) + r.bytes

        # L4 (Protocol)
        proto = get_protocol_name(r.protocol)
        proto_stats[proto] = proto_stats.get(proto, 0) + r.bytes

    # -------------------------
    # HELPER: TOP 5 + OTHER
    # -------------------------
    def top_n_with_other(stats_dict, n=5):
        sorted_items = sorted(stats_dict.items(), key=lambda x: x[1], reverse=True)

        top = sorted_items[:n]
        others = sorted_items[n:]

        result = dict(top)

        other_sum = sum(v for _, v in others)

        if other_sum > 0:
            result["OTHER"] = other_sum

        total = sum(result.values()) or 1

        return [
            {
                "name": k,
                "percentage": round((v / total) * 100, 2)
            }
            for k, v in result.items()
        ]

    # -------------------------
    # FINAL RESPONSE
    # -------------------------
    return {
        "applications": top_n_with_other(app_stats, 5),
        "protocols": top_n_with_other(proto_stats, 5)
    }
#-------------------
# TOP CONVERSATIONS
# ------------------
def get_top_conversations(db, start_time, end_time, event_source=None, interface=None, limit=10):
    q = base_query(db, start_time, end_time, event_source, interface)

    rows = (
        q.with_entities(
            NetFlowRecord.src_ip,
            NetFlowRecord.dst_ip,
            NetFlowRecord.protocol,
            NetFlowRecord.src_port,
            NetFlowRecord.dst_port,
            func.sum(NetFlowRecord.bytes).label("volume")
        )
        .group_by(
            NetFlowRecord.src_ip,
            NetFlowRecord.dst_ip,
            NetFlowRecord.protocol,
            NetFlowRecord.src_port,
            NetFlowRecord.dst_port
        )
        .order_by(func.sum(NetFlowRecord.bytes).desc())
        .limit(limit)
        .all()
    )

    result = []

    for r in rows:
        direction = get_flow_direction(r.src_ip, r.dst_ip)

        # ✅ FIXED LOGIC (CRITICAL)
        if direction == "INBOUND":
            ingress = r.volume
            egress = 0
        elif direction == "OUTBOUND":
            ingress = 0
            egress = r.volume
        else:  # INTERNAL
            ingress = r.volume
            egress = r.volume

        result.append({
            "source_ip": str(r.src_ip),
            "destination_ip": str(r.dst_ip),
            "application": classify_protocol(r.protocol, r.src_port, r.dst_port),

            # ✅ FORMATTED VOLUME
            "volume": format_bytes_struct(r.volume),

            "direction": direction,
            "ingress":format_bytes_struct (ingress),
            "egress": format_bytes_struct(egress)
        })

    return result



def get_dashboard(db, start_time, end_time, event_source=None, interface=None, limit=10):
    q = base_query(db, start_time, end_time, event_source, interface)

    return {
        "real_time": get_real_time(db, start_time, end_time, event_source, interface),
        "timeline": get_timeline(q, start_time, end_time),  # ✅ added
        "traffic_distribution": get_traffic_distribution(db, start_time, end_time, event_source, interface),
        "top_conversations": get_top_conversations(db, start_time, end_time, event_source, interface, limit),
        "protocol_statistics": get_protocol_distribution(db, start_time, end_time, event_source, interface)
    }



def get_explorer_summary(query):
    total_bytes = query.with_entities(func.sum(NetFlowRecord.bytes)).scalar() or 0

    return {
        "matching_flows": query.count(),

        # ✅ improved
        "data_transferred_bytes": total_bytes,
        "data_transferred": format_bytes(total_bytes),

        "unique_sources": query.with_entities(NetFlowRecord.src_ip).distinct().count()
    }



def get_flow_stream(query, limit=50, offset=0):

    rows = query.order_by(NetFlowRecord.flow_start.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()

    flows = defaultdict(lambda: {
        "flow_start": None,
        "flow_end": None,
        "bytes": 0,
        "packets": 0,
        "record": None
    })

    # -------------------------
    # GROUP FLOWS
    # -------------------------
    for r in rows:

        if not r.src_ip or not r.dst_ip or str(r.src_ip) == "0.0.0.0" or str(r.dst_ip) == "0.0.0.0":
            continue

        key = tuple(sorted([
            (str(r.src_ip), r.src_port),
            (str(r.dst_ip), r.dst_port)
        ])) + (r.protocol,)

        f = flows[key]

        if not f["record"]:
            f["record"] = r

        if not f["flow_start"] or r.flow_start < f["flow_start"]:
            f["flow_start"] = r.flow_start

        if r.flow_end:
            if not f["flow_end"] or r.flow_end > f["flow_end"]:
                f["flow_end"] = r.flow_end

        f["bytes"] += r.bytes or 0
        f["packets"] += r.packets or 0

    # -------------------------
    # BUILD RESPONSE
    # -------------------------
    result = []

    for f in flows.values():
        r = f["record"]

        protocol_name = get_protocol_name(r.protocol)

        app = classify_protocol(r.protocol, r.src_port, r.dst_port)
        app = enrich_application(app, str(r.dst_ip))

        # ✅ FIXED duration (ms)
        if f["flow_start"] and f["flow_end"]:
            duration_ms = int((f["flow_end"] - f["flow_start"]).total_seconds() * 1000)
        else:
            duration_ms = 0

        status = get_flow_status(f["flow_start"], f["flow_end"])

        result.append({
            "timestamp": f["flow_start"].strftime("%H:%M:%S.%f")[:-3],
            "source_ip": str(r.src_ip),
            "destination_ip": str(r.dst_ip),
            "source_port": r.src_port if r.src_port else None,
            "destination_port": r.dst_port if r.dst_port else None,
            "protocol": protocol_name,
            "application": app,

            # ✅ FIXED volume
            "volume_bytes": f["bytes"],

            "packets": f["packets"],

            # ✅ FIXED duration
            "duration_ms": duration_ms,

            "status": status,
            "direction": get_flow_direction(r.src_ip, r.dst_ip)
        })

    return result
# -------------------------
# FLOW JOURNEY
# -------------------------

def get_flow_journey(query, top_n=10):

    from collections import defaultdict

    top_sources = (
        query.with_entities(
            NetFlowRecord.src_ip,
            func.sum(NetFlowRecord.bytes).label("total_bytes")
        )
        .group_by(NetFlowRecord.src_ip)
        .order_by(func.sum(NetFlowRecord.bytes).desc())
        .limit(top_n)
        .all()
    )

    top_source_ips = {str(r.src_ip) for r in top_sources}

    filtered_rows = (
        query.filter(NetFlowRecord.src_ip.in_(top_source_ips))
        .order_by(NetFlowRecord.bytes.desc())
        .limit(1000)
        .all()
    )

    sources, destinations = set(), set()
    services = {}
    edges = defaultdict(int)

    total_bytes, total_flows = 0, 0

    for r in filtered_rows:
        app = classify_protocol(r.protocol, r.src_port, r.dst_port)

        src = str(r.src_ip)
        dst = str(r.dst_ip)

        sources.add(src)
        destinations.add(dst)

        # services aggregation
        services.setdefault(app, {"bytes": 0, "flows": 0})
        services[app]["bytes"] += r.bytes
        services[app]["flows"] += 1

        # ✅ NEW edges
        edges[(src, dst)] += r.bytes

        total_bytes += r.bytes
        total_flows += 1

    return {
        "sources": list(sources),
        "destinations": list(destinations),

        "services": [
            {"name": k, "bytes": v["bytes"], "flows": v["flows"]}
            for k, v in services.items()
        ],

        # ✅ NEW graph structure
        "edges": [
            {
                "source": src,
                "destination": dst,
                "bytes": bytes_val
            }
            for (src, dst), bytes_val in edges.items()
        ],

        "total_bytes": total_bytes,
        "total_flows": total_flows
    }

# -------------------------
# EXPLORER MAIN
# -------------------------


def get_explorer(
    db,
    start_time,
    end_time,
    event_source=None,
    interface=None,
    source_ip=None,
    destination_ip=None,
    port=None,
    protocol=None,
    limit=50,
    page=1
):
    query = base_query(db, start_time, end_time, event_source, interface)
    query = apply_explorer_filters(query, source_ip, destination_ip, port, protocol)

    total = query.count()

    offset = (page - 1) * limit

    return {
        "summary": get_explorer_summary(query),

        # ✅ pagination applied
        "flow_stream": get_flow_stream(query, limit=limit, offset=offset),

        "flow_journey": get_flow_journey(query),

        # ✅ NEW pagination block
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit
        }
    }
# =========================
# ANALYTICS MAIN
# =========================



def get_analytics(
    db,
    start_time,
    end_time,
    event_source=None,
    interface=None
):
    query = base_query(db, start_time, end_time, event_source, interface)

    # ✅ FIRST create this
    performance_trends = get_performance_trends(query, start_time, end_time)

    return {
        "flow_overview": get_flow_overview(query, start_time, end_time),

        # ✅ use same variable
        "performance_trends": performance_trends,

        "top_talkers": get_top_talkers(query),

        "traffic_distribution": get_traffic_distribution(
            db, start_time, end_time, event_source, interface
        ),

        "pattern_recognition": get_pattern_recognition(query),

        "latency_distribution": get_latency_distribution(query),

        # ✅ NOW it works
        "anomalies": detect_anomalies(performance_trends),

        "intelligent_insights": get_intelligent_insights(query)
    }