from app.db_utils import safe_commit
import socket
import logging
import queue
import threading
from database import SessionLocal
from app.syslog.parser import parse_syslog
from app.syslog.crud import insert_syslog

SYSLOG_PORT = 514
BUFFER_SIZE = 4096

logger = logging.getLogger("syslog.listener")

log_queue = queue.Queue(maxsize=10000)


def listener_thread():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", SYSLOG_PORT))

    logger.info("Syslog listener started on port %s", SYSLOG_PORT)

    while True:
        data, addr = sock.recvfrom(BUFFER_SIZE)

        try:
            log_queue.put_nowait((data, addr))   
        except queue.Full:
            logger.warning(
                "Syslog queue full — dropping packet from %s",
                addr[0]
            )


def db_worker_thread():
    db = SessionLocal()   

    logger.info(" Syslog DB worker started")

    while True:
        data, addr = log_queue.get()

        try:
            raw_message = data.decode(errors="ignore")[:2048]
            parsed = parse_syslog(raw_message, addr[0])

            insert_syslog(db, parsed)

        except Exception as exc:
            db.rollback()
            logger.error("Syslog insert failed: %s", exc)


def run():
    #  Start worker thread
    threading.Thread(target=db_worker_thread, daemon=True).start()

    # Start listener (blocking)
    listener_thread()


if __name__ == "__main__":
    run()