
from fastapi import FastAPI
import threading
import logging
from contextlib import asynccontextmanager

# DB
from database import engine, Base

# Syslog
from app.syslog.router import router as syslog_router
from app.syslog.listener import run as start_syslog_listener

# Flow
from app.flows.netflow import start_netflow_listener
from app.flows.sflow import start_sflow_listener
from app.flows.ipfix import start_ipfix_listener
from app.flows.router import router as flow_router

# Path Analysis
from app.path_analysis.routes import router as path_router


# ✅ Logger setup
logger = logging.getLogger("nms.main")
logging.basicConfig(level=logging.INFO)


# =====================================================
# ✅ LIFESPAN (REPLACES @app.on_event)
# =====================================================
@asynccontextmanager
async def lifespan(app: FastAPI):

    # -------------------------
    # STARTUP
    # -------------------------
    threading.Thread(target=start_syslog_listener, daemon=True).start()
    logger.info("🚀 Syslog Collector started")

    threading.Thread(target=start_netflow_listener, daemon=True).start()
    logger.info("🚀 NetFlow Listener started")

    try:
        threading.Thread(target=start_sflow_listener, daemon=True).start()
        logger.info("🚀 sFlow Listener started")
    except Exception:
        logger.warning("⚠️ sFlow not started")

    threading.Thread(target=start_ipfix_listener, daemon=True).start()
    logger.info("🚀 IPFIX Listener started")

    yield

    # -------------------------
    # SHUTDOWN (optional)
    # -------------------------
    logger.info("Shutting down application...")


# =====================================================
# APP INIT
# =====================================================
app = FastAPI(
    title="NMS Backend",
    version="1.0.0",
    lifespan=lifespan
)


# ✅ Create tables
Base.metadata.create_all(bind=engine)


# =====================================================
# ROOT
# =====================================================
@app.get("/")
def root():
    return {"message": "NMS Backend Running 🚀"}


# =====================================================
# ROUTES
# =====================================================
app.include_router(syslog_router, prefix="/syslog")
app.include_router(flow_router, prefix="/flow", tags=["Flow Dashboard"])
app.include_router(path_router, prefix="/path-analysis", tags=["Path Analysis"])