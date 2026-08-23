"""
鉴权与当前用户工具
"""
from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.models import User


def get_current_user():
    """从 JWT 解析当前用户对象"""
    user_id = get_jwt_identity()
    if user_id is None:
        return None
    return User.query.get(int(user_id))


def role_required(*roles):
    """角色权限装饰器"""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = get_current_user()
            if user is None:
                return jsonify({"code": 401, "message": "未登录或登录已过期", "data": None}), 401
            if roles and user.role not in roles:
                return jsonify({"code": 403, "message": "无权限执行该操作", "data": None}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator
