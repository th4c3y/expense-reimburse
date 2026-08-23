"""
认证接口：登录、获取当前用户、修改密码
"""
from flask import request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
)

from app import db
from app.models import User
from app.utils import error, success
from app.utils.auth import get_current_user

auth_bp = __import__("flask").Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return error("用户名和密码不能为空")
    user = User.query.filter_by(username=username).first()
    if user is None or not user.verify_password(password):
        return error("用户名或密码错误", code=401)
    if user.status != 1:
        return error("账号已被禁用，请联系管理员", code=403)
    token = create_access_token(identity=str(user.id))
    return success(
        {
            "token": token,
            "user": user.to_dict(),
        },
        message="登录成功",
    )


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user = get_current_user()
    if user is None:
        return error("用户不存在", code=401)
    return success(user.to_dict())


@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    old_pwd = data.get("old_password")
    new_pwd = data.get("new_password")
    if not user.verify_password(old_pwd):
        return error("原密码错误")
    if not new_pwd or len(new_pwd) < 6:
        return error("新密码长度至少 6 位")
    user.password = new_pwd
    db.session.commit()
    return success(message="密码修改成功")
