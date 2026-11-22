"""System info and health endpoints."""
import os
import platform
import socket
from datetime import datetime, timezone

import psutil
from flask_jwt_extended import jwt_required
from flask_restx import Namespace, Resource

ns = Namespace("system", description="Host information", path="/system")
health_ns = Namespace("health", description="Liveness check", path="/")

# docker-compose bind-mounts these read-only so the dashboard shows the EC2 host,
# not the container. Outside Docker the normal system files are used.
HOST_OS_RELEASE = "/host/etc/os-release"
HOST_HOSTNAME = "/host/etc/hostname"


def _first_existing(*paths):
    for path in paths:
        if os.path.isfile(path):
            return path
    return None


def _hostname():
    path = _first_existing(HOST_HOSTNAME)
    if path:
        with open(path, encoding="utf-8") as handle:
            value = handle.read().strip()
            if value:
                return value
    return socket.gethostname()


def _os_name():
    path = _first_existing(HOST_OS_RELEASE, "/etc/os-release")
    if path:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
    return platform.platform()


@ns.route("/info")
class SystemInfo(Resource):
    @jwt_required()
    @ns.doc(security="Bearer")
    @ns.response(401, "Missing or invalid token")
    def get(self):
        """Hostname, OS, kernel version and uptime."""
        boot = datetime.fromtimestamp(psutil.boot_time(), tz=timezone.utc)
        uptime = (datetime.now(timezone.utc) - boot).total_seconds()
        return {
            "hostname": _hostname(),
            "os": _os_name(),
            "kernel": platform.release(),
            "architecture": platform.machine(),
            "cpu_count": psutil.cpu_count(logical=True),
            "memory_total_gb": round(psutil.virtual_memory().total / 1024 ** 3, 2),
            "uptime_seconds": int(uptime),
            "boot_time": boot.isoformat().replace("+00:00", "Z"),
        }


@health_ns.route("/health")
class Health(Resource):
    def get(self):
        """Health check (no auth)."""
        return {"status": "ok"}
