"""Registration and login."""
import re

from flask_jwt_extended import create_access_token
from flask_restx import Namespace, Resource, fields
from sqlalchemy.exc import IntegrityError

from models import User, db

ns = Namespace("auth", description="Registration and login", path="/auth")

credentials = ns.model(
    "Credentials",
    {
        "email": fields.String(required=True, example="you@example.com"),
        "password": fields.String(required=True, min_length=8, example="a-strong-password"),
    },
)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _read_credentials():
    data = ns.payload or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    return email, password


def _token_for(user):
    return create_access_token(identity=str(user.id))


@ns.route("/register")
class Register(Resource):
    @ns.expect(credentials, validate=True)
    @ns.response(201, "User created")
    @ns.response(400, "Invalid input or email already registered")
    def post(self):
        """Create a user and return a JWT (auto-login)."""
        email, password = _read_credentials()
        if not EMAIL_RE.match(email) or len(email) > 255:
            return {"error": "Enter a valid email address"}, 400
        if len(password) < 8:
            return {"error": "Password must be at least 8 characters"}, 400
        if User.query.filter_by(email=email).first():
            return {"error": "That email is already registered"}, 400

        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {"error": "That email is already registered"}, 400

        return {"message": "User created", "email": email,
                "access_token": _token_for(user)}, 201


@ns.route("/login")
class Login(Resource):
    @ns.expect(credentials, validate=True)
    @ns.response(200, "JWT issued")
    @ns.response(401, "Invalid email or password")
    def post(self):
        """Verify credentials and return a JWT."""
        email, password = _read_credentials()
        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(password):
            return {"error": "Invalid email or password"}, 401
        return {"email": email, "access_token": _token_for(user)}, 200
