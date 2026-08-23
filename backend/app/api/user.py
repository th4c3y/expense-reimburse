"""
用户管理接口（管理员）
"""
from flask import request

from app import db
from app.models import User, Department
from app.utils import error, success
from app.utils.auth import role_required

user_bp = __import__("flask").Blueprint("user", __name__)


@user_bp.route("", methods=["GET"])
@role_required("admin")
def list_users():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    keyword = request.args.get("keyword", "").strip()
    query = User.query
    if keyword:
        query = query.filter(
            User.username.like(f"%{keyword}%") | User.real_name.like(f"%{keyword}%")
        )
    pagination = query.order_by(User.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return success(
        {
            "items": [u.to_dict() for u in pagination.items],
            "total": pagination.total,
            "page": page,
            "per_page": per_page,
        }
    )


@user_bp.route("", methods=["POST"])
@role_required("admin")
def create_user():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    real_name = data.get("real_name")
    password = data.get("password", "123456")
    if not username or not real_name:
        return error("用户名和真实姓名必填")
    if User.query.filter_by(username=username).first():
        return error("用户名已存在")
    user = User(
        username=username,
        real_name=real_name,
        email=data.get("email"),
        phone=data.get("phone"),
        department_id=data.get("department_id"),
        role=data.get("role", User.ROLE_EMPLOYEE),
        approval_limit=data.get("approval_limit", 0),
    )
    user.password = password
    db.session.add(user)
    db.session.commit()
    return success(user.to_dict(), message="创建成功")


@user_bp.route("/<int:user_id>", methods=["PUT"])
@role_required("admin")
def update_user(user_id):
    user = User.query.get(user_id)
    if user is None:
        return error("用户不存在")
    data = request.get_json(silent=True) or {}
    for field in ["real_name", "email", "phone", "department_id", "role", "approval_limit"]:
        if field in data:
            setattr(user, field, data[field])
    if data.get("password"):
        user.password = data["password"]
    if "status" in data:
        user.status = data["status"]
    db.session.commit()
    return success(user.to_dict(), message="更新成功")


@user_bp.route("/<int:user_id>", methods=["DELETE"])
@role_required("admin")
def delete_user(user_id):
    user = User.query.get(user_id)
    if user is None:
        return error("用户不存在")
    db.session.delete(user)
    db.session.commit()
    return success(message="删除成功")


@user_bp.route("/simple", methods=["GET"])
@role_required()
def simple_users():
    """下拉选择器使用的精简用户列表"""
    users = User.query.filter_by(status=1).all()
    return success(
        [{"id": u.id, "real_name": u.real_name, "role": u.role} for u in users]
    )
