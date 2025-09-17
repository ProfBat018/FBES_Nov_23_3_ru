from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from marshmallow import ValidationError
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from ..ext import db
from ..models import User
from ..schemas import RegisterSchema, LoginSchema, UserOutSchema
from flask_smorest import Blueprint


bp = Blueprint("Users", "users", url_prefix="/api/v1", description="User operations")

_reg = RegisterSchema()
_log = LoginSchema()
_user_out = UserOutSchema()

@bp.get("/healthz")
def healthz():
    return {"status": "ok"}, 200

@bp.post("/auth/register")
def register():
    try:
        data = _reg.load(request.get_json() or {})
    except ValidationError as e:
        return {"errors": e.messages}, 400
    u = User(email=data["email"], name=data["name"],
             password_hash=generate_password_hash(data["password"]))
    db.session.add(u)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {"message": "Email already exists"}, 409
    return _user_out.dump(u), 201

@bp.post("/auth/login")
def login():
    try:
        data = _log.load(request.get_json() or {})
    except ValidationError as e:
        return {"errors": e.messages}, 400
    u = User.query.filter_by(email=data["email"]).first()
    if not u or not check_password_hash(u.password_hash, data["password"]):
        return {"message": "Invalid credentials"}, 401
    token = create_access_token(identity=str(u.id))
    return {"access_token": token}

@bp.get("/me")
@jwt_required()
def me():
    uid = get_jwt_identity()
    u = User.query.get(uid)
    return _user_out.dump(u), 200
