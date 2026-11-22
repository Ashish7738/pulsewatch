"""PulseWatch Flask application factory."""
import logging

from flask import Blueprint, Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_jwt_extended.exceptions import JWTExtendedException
from flask_restx import Api
from jwt.exceptions import PyJWTError
from werkzeug.exceptions import HTTPException

from collector import start_collector
from config import load_config
from models import db
from routes import auth, metrics, system

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app(test_config=None):
    app = Flask(__name__)

    if test_config is None:
        app.config.update(load_config())
    else:
        app.config.update(
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            SAMPLE_INTERVAL_SECONDS=10,
            RETENTION_DAYS=7,
            START_COLLECTOR=False,
        )
        app.config.update(test_config)

    db.init_app(app)
    jwt = JWTManager(app)

    # --- JSON error bodies for JWT problems (401) ---
    @jwt.unauthorized_loader
    def missing_token(reason):
        return jsonify(error=reason, status=401), 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return jsonify(error=reason, status=401), 401

    @jwt.expired_token_loader
    def expired_token(_header, _payload):
        return jsonify(error="Token has expired, log in again", status=401), 401

    # --- REST API + Swagger at /api/docs ---
    blueprint = Blueprint("api", __name__, url_prefix="/api")
    api = Api(
        blueprint,
        title="PulseWatch API",
        version="1.0",
        description="Live CPU, memory and disk metrics for the host this runs on.",
        doc="/docs",
        authorizations={
            "Bearer": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": "Paste: Bearer <your JWT>",
            }
        },
    )
    api.add_namespace(auth.ns)
    api.add_namespace(metrics.ns)
    api.add_namespace(system.ns)
    api.add_namespace(system.health_ns)

    @api.errorhandler(Exception)
    def handle_api_error(err):
        if isinstance(err, (JWTExtendedException, PyJWTError)):
            return {"error": str(err) or "Unauthorized", "status": 401}, 401
        if isinstance(err, HTTPException):
            data = getattr(err, "data", None) or {}
            body = {"error": data.get("message") or err.description,
                    "status": err.code or 500}
            if data.get("errors"):
                body["details"] = data["errors"]
            return body, err.code or 500
        app.logger.exception("Unhandled error in API")
        return {"error": "Internal server error", "status": 500}, 500

    app.register_blueprint(blueprint)

    # --- JSON error bodies outside the API blueprint ---
    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return jsonify(error=err.description, status=err.code), err.code

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        app.logger.exception("Unhandled error")
        return jsonify(error="Internal server error", status=500), 500

    with app.app_context():
        db.create_all()

    if app.config.get("START_COLLECTOR"):
        start_collector(app)

    return app
