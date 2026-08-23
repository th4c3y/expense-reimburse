"""
部门管理接口（管理员）
"""
from flask import request

from app import db
from app.models import Department
from app.utils import error, success
from app.utils.auth import role_required

dept_bp = __import__("flask").Blueprint("department", __name__)


@dept_bp.route("", methods=["GET"])
@role_required()
def list_departments():
    depts = Department.query.order_by(Department.id).all()
    return success([d.to_dict() for d in depts])


@dept_bp.route("", methods=["POST"])
@role_required("admin")
def create_department():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    code = data.get("code")
    if not name or not code:
        return error("部门名称和编码必填")
    if Department.query.filter_by(code=code).first():
        return error("部门编码已存在")
    dept = Department(
        name=name,
        code=code,
        manager_id=data.get("manager_id"),
        description=data.get("description"),
    )
    db.session.add(dept)
    db.session.commit()
    return success(dept.to_dict(), message="创建成功")


@dept_bp.route("/<int:dept_id>", methods=["PUT"])
@role_required("admin")
def update_department(dept_id):
    dept = Department.query.get(dept_id)
    if dept is None:
        return error("部门不存在")
    data = request.get_json(silent=True) or {}
    for field in ["name", "code", "manager_id", "description"]:
        if field in data:
            setattr(dept, field, data[field])
    db.session.commit()
    return success(dept.to_dict(), message="更新成功")


@dept_bp.route("/<int:dept_id>", methods=["DELETE"])
@role_required("admin")
def delete_department(dept_id):
    dept = Department.query.get(dept_id)
    if dept is None:
        return error("部门不存在")
    db.session.delete(dept)
    db.session.commit()
    return success(message="删除成功")
