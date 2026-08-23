"""
审批流配置接口：审批流与节点的增删改查
"""
from flask import request

from app import db
from app.models import ApprovalFlow, ApprovalNode
from app.utils import error, success
from app.utils.auth import role_required

flow_bp = __import__("flask").Blueprint("approval_flow", __name__)


@flow_bp.route("", methods=["GET"])
@role_required("admin")
def list_flows():
    flows = ApprovalFlow.query.order_by(ApprovalFlow.priority.desc()).all()
    return success([f.to_dict() for f in flows])


@flow_bp.route("", methods=["POST"])
@role_required("admin")
def create_flow():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    if not name:
        return error("审批流名称必填")
    flow = ApprovalFlow(
        name=name,
        description=data.get("description"),
        priority=data.get("priority", 0),
        min_amount=data.get("min_amount", 0),
        max_amount=data.get("max_amount"),
        department_scope=data.get("department_scope", ""),
        is_default=data.get("is_default", 0),
        status=data.get("status", 1),
    )
    db.session.add(flow)
    db.session.flush()

    for i, n in enumerate(data.get("nodes", []), start=1):
        node = ApprovalNode(
            flow_id=flow.id,
            order_no=i,
            name=n.get("name", f"节点{i}"),
            approver_type=n.get("approver_type", "role"),
            approver_value=n.get("approver_value"),
        )
        db.session.add(node)
    # 若设为默认，取消其他默认
    if flow.is_default:
        ApprovalFlow.query.filter(ApprovalFlow.id != flow.id).update(
            {"is_default": 0}
        )
    db.session.commit()
    return success(flow.to_dict(), message="创建成功")


@flow_bp.route("/<int:flow_id>", methods=["PUT"])
@role_required("admin")
def update_flow(flow_id):
    flow = ApprovalFlow.query.get(flow_id)
    if flow is None:
        return error("审批流不存在")
    data = request.get_json(silent=True) or {}
    for field in [
        "name", "description", "priority", "min_amount",
        "max_amount", "department_scope", "is_default", "status"
    ]:
        if field in data:
            setattr(flow, field, data[field])

    # 全量替换节点
    if "nodes" in data:
        for old in flow.nodes.all():
            db.session.delete(old)
        for i, n in enumerate(data["nodes"], start=1):
            node = ApprovalNode(
                flow_id=flow.id,
                order_no=i,
                name=n.get("name", f"节点{i}"),
                approver_type=n.get("approver_type", "role"),
                approver_value=n.get("approver_value"),
            )
            db.session.add(node)
    if flow.is_default:
        ApprovalFlow.query.filter(ApprovalFlow.id != flow.id).update(
            {"is_default": 0}
        )
    db.session.commit()
    return success(flow.to_dict(), message="更新成功")


@flow_bp.route("/<int:flow_id>", methods=["DELETE"])
@role_required("admin")
def delete_flow(flow_id):
    flow = ApprovalFlow.query.get(flow_id)
    if flow is None:
        return error("审批流不存在")
    db.session.delete(flow)
    db.session.commit()
    return success(message="删除成功")
