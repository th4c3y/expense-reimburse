"""
审批接口：审批中心列表、通过、驳回、付款
"""
from flask import request

from app import db
from app.models import (
    ExpenseSheet,
    ApprovalRecord,
    User,
    Department,
)
from app.utils import error, success
from app.utils.auth import get_current_user, role_required

approval_bp = __import__("flask").Blueprint("approval", __name__)


@approval_bp.route("/pending", methods=["GET"])
@role_required("manager", "finance", "admin")
def pending_list():
    """
    待我审批列表：依据报销单当前节点配置动态解析审批人，
    仅展示当前登录用户属于该节点审批人的单据（admin 可看全部）。
    """
    user = get_current_user()
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 15))
    query = ExpenseSheet.query.filter(ExpenseSheet.status == ExpenseSheet.STATUS_PENDING)

    if user.role != "admin":
        # 仅展示当前用户为节点审批人的单据
        candidate_ids = []
        for s in query.all():
            node = s.get_current_node()
            if not node:
                continue
            approvers = s.resolve_approvers(node)
            if user.id in [a.id for a in approvers]:
                candidate_ids.append(s.id)
        query = ExpenseSheet.query.filter(ExpenseSheet.id.in_(candidate_ids)) if candidate_ids else ExpenseSheet.query.filter(False)

    pagination = query.order_by(ExpenseSheet.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    items = []
    for s in pagination.items:
        d = s.to_dict()
        d["applicant_name"] = s.applicant.real_name if s.applicant else None
        node = s.get_current_node()
        d["current_node_name"] = node.name if node else "—"
        items.append(d)
    return success(
        {
            "items": items,
            "total": pagination.total,
            "page": page,
            "per_page": per_page,
        }
    )


@approval_bp.route("/<int:sheet_id>/approve", methods=["POST"])
@role_required("manager", "finance", "admin")
def approve(sheet_id):
    sheet = ExpenseSheet.query.get(sheet_id)
    if sheet is None:
        return error("报销单不存在")
    if sheet.status != ExpenseSheet.STATUS_PENDING:
        return error("单据不在审批中")
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    comment = data.get("comment", "")

    # 当前节点权限校验：当前用户必须属于该节点审批人
    node = sheet.get_current_node()
    if node is None:
        return error("未找到审批节点配置")
    approvers = s_resolve = sheet.resolve_approvers(node)
    if user.role != "admin" and user.id not in [a.id for a in approvers]:
        return error("您不是当前节点的审批人，无权审批")

    rec = ApprovalRecord(
        sheet_id=sheet.id,
        approver_id=user.id,
        node=sheet.current_node,
        action=ApprovalRecord.ACTION_APPROVE,
        comment=comment,
        before_status=sheet.status,
    )

    # 判断是否还有下一节点
    flow = node.flow
    from app.models import ApprovalNode as _AN
    next_node = (
        _AN.query.filter_by(flow_id=flow.id)
        .filter(_AN.order_no > node.order_no)
        .order_by(_AN.order_no)
        .first()
    )

    if next_node:
        sheet.current_node = next_node.order_no
        sheet.status = ExpenseSheet.STATUS_PENDING
        rec.after_status = ExpenseSheet.STATUS_PENDING
    else:
        sheet.status = ExpenseSheet.STATUS_APPROVED
        sheet.approved_at = db.func.now()
        rec.after_status = ExpenseSheet.STATUS_APPROVED
    db.session.add(rec)
    db.session.commit()
    return success(sheet.to_dict(), message="审批通过")


@approval_bp.route("/<int:sheet_id>/reject", methods=["POST"])
@role_required("manager", "finance", "admin")
def reject(sheet_id):
    sheet = ExpenseSheet.query.get(sheet_id)
    if sheet is None:
        return error("报销单不存在")
    if sheet.status != ExpenseSheet.STATUS_PENDING:
        return error("单据不在审批中")
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    comment = data.get("comment", "")
    if not comment:
        return error("驳回必须填写驳回意见")

    # 节点权限校验
    node = sheet.get_current_node()
    if node is None:
        return error("未找到审批节点配置")
    approvers = sheet.resolve_approvers(node)
    if user.role != "admin" and user.id not in [a.id for a in approvers]:
        return error("您不是当前节点的审批人，无权审批")

    rec = ApprovalRecord(
        sheet_id=sheet.id,
        approver_id=user.id,
        node=sheet.current_node,
        action=ApprovalRecord.ACTION_REJECT,
        comment=comment,
        before_status=sheet.status,
        after_status=ExpenseSheet.STATUS_REJECTED,
    )
    sheet.status = ExpenseSheet.STATUS_REJECTED
    sheet.reject_reason = comment
    db.session.add(rec)
    db.session.commit()
    return success(sheet.to_dict(), message="已驳回")


@approval_bp.route("/<int:sheet_id>/pay", methods=["POST"])
@role_required("finance", "admin")
def pay(sheet_id):
    """财务付款确认 -> 已付款"""
    sheet = ExpenseSheet.query.get(sheet_id)
    if sheet is None:
        return error("报销单不存在")
    if sheet.status != ExpenseSheet.STATUS_APPROVED:
        return error("仅审批通过的单据可以付款")
    sheet.status = ExpenseSheet.STATUS_PAID
    sheet.paid_at = db.func.now()
    db.session.commit()
    return success(sheet.to_dict(), message="付款成功")


@approval_bp.route("/<int:sheet_id>/records", methods=["GET"])
@role_required()
def records(sheet_id):
    recs = (
        ApprovalRecord.query.filter_by(sheet_id=sheet_id)
        .order_by(ApprovalRecord.id)
        .all()
    )
    result = []
    for r in recs:
        d = r.to_dict()
        approver = User.query.get(r.approver_id)
        d["approver_name"] = approver.real_name if approver else None
        result.append(d)
    return success(result)
