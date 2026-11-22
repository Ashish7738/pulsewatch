"""Background sampler: reads host metrics with psutil and stores them."""
import logging
import threading
import time
from datetime import timedelta

import psutil

from models import Metric, db, utcnow

log = logging.getLogger("pulsewatch.collector")

_lock = threading.Lock()
_started = False
CLEANUP_EVERY_SECONDS = 3600


def sample(cpu_interval=1):
    """Return one reading of CPU, memory and disk usage (percent)."""
    return {
        "cpu": psutil.cpu_percent(interval=cpu_interval),
        "memory": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("/").percent,
    }


def store_sample():
    reading = sample()
    db.session.add(Metric(**reading))
    db.session.commit()
    return reading


def cleanup(retention_days):
    """Delete metric rows older than the retention window."""
    cutoff = utcnow() - timedelta(days=retention_days)
    deleted = Metric.query.filter(Metric.ts < cutoff).delete()
    db.session.commit()
    if deleted:
        log.info("Deleted %s metric rows older than %s days", deleted, retention_days)


def _run(app):
    interval = app.config["SAMPLE_INTERVAL_SECONDS"]
    retention = app.config["RETENTION_DAYS"]
    last_cleanup = None

    while True:
        try:
            with app.app_context():
                now = time.monotonic()
                if last_cleanup is None or now - last_cleanup >= CLEANUP_EVERY_SECONDS:
                    cleanup(retention)
                    last_cleanup = now
                store_sample()
        except Exception:  # keep the sampler alive on transient DB errors
            log.exception("Metric collection failed")
        time.sleep(max(1, interval - 1))  # sampling itself takes ~1s


def start_collector(app):
    """Start the sampler thread once per process."""
    global _started
    with _lock:
        if _started:
            return
        thread = threading.Thread(
            target=_run, args=(app,), name="metric-collector", daemon=True
        )
        thread.start()
        _started = True
        log.info("Metric collector started")
