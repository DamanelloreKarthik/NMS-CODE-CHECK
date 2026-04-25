
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class TopTalker(BaseModel):
    src_ip: str
    dst_ip: Optional[str]
    total_bytes: int


class PathNode(BaseModel):
    source: str
    destination: str
    bytes: int


class PathAnalysisResponse(BaseModel):
    device_ip: str
    start_time: datetime
    end_time: datetime
    paths: List[PathNode]


class FlowRecordOut(BaseModel):
    exporter_ip: str
    src_ip: str
    dst_ip: str
    protocol: int
    src_port: Optional[int]
    dst_port: Optional[int]
    packets: int
    bytes: int
    flow_start: datetime
    flow_end: datetime