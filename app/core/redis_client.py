from app.db_utils import safe_commit
import redis
import json

redis_client = redis.Redis(
    host="localhost",
    port= 6381,
    decode_responses=True
)

# IPFIX
def save_ipfix_template(exporter_ip, domain_id, template_id, fields):
    key = f"nms:ipfix:{exporter_ip}:{domain_id}:{template_id}"
    redis_client.set(key, json.dumps(fields), ex=3600)


def get_ipfix_template(exporter_ip, domain_id, template_id):
    key = f"nms:ipfix:{exporter_ip}:{domain_id}:{template_id}"
    data = redis_client.get(key)
    return json.loads(data) if data else None


# NETFLOW V9
def save_v9_template(exporter_ip, template_id, fields):
    key = f"nms:netflow:{exporter_ip}:{template_id}"
    redis_client.set(key, json.dumps(fields), ex=3600)


def get_v9_template(exporter_ip, template_id):
    key = f"nms:netflow:{exporter_ip}:{template_id}"
    data = redis_client.get(key)
    return json.loads(data) if data else None