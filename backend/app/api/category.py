"""
报销类别管理接口
"""
from flask import request

from app import db
from app.models import ExpenseCategory
from app.utils import error, success
from app.utils.auth import role_required

category_bp = __import__("flask").Blueprint("category", __name__)


@category_bp.route("", methods=["GET"])
@role_required()
def list_categories():
    cats = ExpenseCategory.query.filter_by(status=1).order_by(ExpenseCategory.id).all()
    return success([c.to_dict() for c in cats])


@category_bp.route("", methods=["POST"])
@role_required("admin", "finance")
def create_category():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    code = data.get("code")
    if not name or not code:
        return error("类别名称和编码必填")
    if ExpenseCategory.query.filter_by(code=code).first():
        return error("类别编码已存在")
    cat = ExpenseCategory(
        name=name, code=code, description=data.get("description")
    )
    db.session.add(cat)
    db.session.commit()
    return success(cat.to_dict(), message="创建成功")


@category_bp.route("/<int:cat_id>", methods=["PUT"])
@role_required("admin", "finance")
def update_category(cat_id):
    cat = ExpenseCategory.query.get(cat_id)
    if cat is None:
        return error("类别不存在")
    data = request.get_json(silent=True) or {}
    for field in ["name", "code", "description", "status"]:
        if field in data:
            setattr(cat, field, data[field])
    db.session.commit()
    return success(cat.to_dict(), message="更新成功")


@category_bp.route("/<int:cat_id>", methods=["DELETE"])
@role_required("admin", "finance")
def delete_category(cat_id):
    cat = ExpenseCategory.query.get(cat_id)
    if cat is None:
        return error("类别不存在")
    db.session.delete(cat)
    db.session.commit()
    return success(message="删除成功")
