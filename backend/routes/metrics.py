"""Metric endpoints."""
from datetime import timedelta

from flask_jwt_extended import jwt_required
from flask_restx import Namespace, Resource, fields, reqparse

from collector import sample
from models import Metric, utcnow

ns = Namespace("metrics", description="CPU, memory and disk usage", path="/metrics")

metric_model = ns.model(
    "Metric",
    {
        "timestamp": fields.String(example="2026-01-01T12:00:00Z"),
        "cpu": fields.Float(description="CPU usage %"),
        "memory": fields.Float(description="Memory usage %"),
        "disk": fields.Float(description="Disk usage %"),
    },
)

history_parser = reqparse.RequestParser()
history_parser.add_argument(
    "minutes", type=int, default=60, location="args",
    help="How many minutes of history to return (1-10080)",
)

MAX_MINUTES = 7 * 24 * 60


@ns.route("/latest")
class Latest(Resource):
    @jwt_required()
    @ns.doc(security="Bearer")
    @ns.response(401, "Missing or invalid token")
    @ns.marshal_with(metric_model)
    def get(self):
        """Most recent CPU / memory / disk sample."""
        row = Metric.query.order_by(Metric.ts.desc()).first()
        if row is not None:
            return row.to_dict()
        # Collector has not stored anything yet: take a live reading.
        reading = sample(cpu_interval=0.2)
        reading["timestamp"] = utcnow().isoformat() + "Z"
        return reading


@ns.route("/history")
class History(Resource):
    @jwt_required()
    @ns.doc(security="Bearer")
    @ns.expect(history_parser)
    @ns.response(400, "Invalid minutes value")
    @ns.response(401, "Missing or invalid token")
    def get(self):
        """Historical samples, oldest first."""
        minutes = history_parser.parse_args()["minutes"]
        if minutes is None or not 1 <= minutes <= MAX_MINUTES:
            return {"error": f"minutes must be between 1 and {MAX_MINUTES}"}, 400

        cutoff = utcnow() - timedelta(minutes=minutes)
        rows = (
            Metric.query.filter(Metric.ts >= cutoff).order_by(Metric.ts.asc()).all()
        )
        return {"minutes": minutes, "count": len(rows),
                "samples": [row.to_dict() for row in rows]}
