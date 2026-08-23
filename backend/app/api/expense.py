"""
报销单接口：增删改查、明细、提交
"""
import datetime

from flask import request

from app import db
from app.models import (
    ExpenseSheet,
    ExpenseItem,
    ExpenseCategory,
    Department,
)
from app.utils import error, success
from app.utils.auth import get_current_user, role_required

expense_bp = __import__("flask").Blueprint("expense", __name__)


def _gen_sheet_no():
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    count = ExpenseSheet.query.filter(
        ExpenseSheet.sheet_no.like(f"BX{date_str}%")
    ).count()
    return f"BX{date_str}{str(count + 1).zfill(4)}"


def _recalc_total(sheet):
    total = sum(float(i.amount) for i in sheet.items.all())
    sheet.total_amount = total


@expense_bp.route("", methods=["GET"])
@role_required()
def list_sheets():
    user = get_current_user()
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 15))
    status = request.args.get("status")
    keyword = request.args.get("keyword", "").strip()

    query = ExpenseSheet.query
    # 普通员工只能看自己的；经理/财务/管理员看全部
    if user.role == "employee":
        query = query.filter_by(applicant_id=user.id)
    if status:
        query = query.filter(ExpenseSheet.status == status)
    if keyword:
        query = query.filter(ExpenseSheet.title.like(f"%{keyword}%"))

    pagination = query.order_by(ExpenseSheet.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    items = []
    for s in pagination.items:
        d = s.to_dict()
        d["applicant_name"] = s.applicant.real_name if s.applicant else None
        items.append(d)
    return success(
        {
            "items": items,
            "total": pagination.total,
            "page": page,
            "per_page": per_page,
        }
    )


@expense_bp.route("/<int:sheet_id>", methods=["GET"])
@role_required()
def get_sheet(sheet_id):
    sheet = ExpenseSheet.query.get(sheet_id)
    if sheet is None:
        return error("报销单不存在")
    user = get_current_user()
    if user.role == "employee" and sheet.applicant_id != user.id:
        return error("无权查看该单据", code=403)
    d = sheet.to_dict(with_items=True)
    d["applicant_name"] = sheet.applicant.real_name if sheet.applicant else None
    d["department_name"] = (
        sheet.department.name if sheet.department else None
    )
    d["items"] = []
    for item in sheet.items.all():
        ic = item.to_dict()
        cat = ExpenseCategory.query.get(item.category_id)
        ic["category_name"] = cat.name if cat else None
        d["items"].append(ic)
    return success(d)


@expense_bp.route("", methods=["POST"])
@role_required()
def create_sheet():
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    sheet = ExpenseSheet(
        sheet_no=_gen_sheet_no(),
        applicant_id=user.id,
        department_id=user.department_id,
        title=data.get("title", "未命名报销单"),
        reason=data.get("reason"),
        status=ExpenseSheet.STATUS_DRAFT,
    )
    db.session.add(sheet)
    db.session.flush()
    for it in data.get("items", []):
        item = ExpenseItem(
            sheet_id=sheet.id,
            category_id=it["category_id"],
            amount=it["amount"],
            occur_date=datetime.date.fromisoformat(it["occur_date"]),
            description=it.get("description"),
            invoice_no=it.get("invoice_no"),
            remark=it.get("remark"),
        )
        db.session.add(item)
    _recalc_total(sheet)
    db.session.commit()
    return success(sheet.to_dict(with_items=True), message="保存成功")


@expense_bp.route("/<int:sheet_id>", methods=["PUT"])
@role_required()
def update_sheet(sheet_id):
    sheet = ExpenseSheet.query.get(sheet_id)
    if sheet is None:
        return error("报销单不存在")
    user = get_current_user()
    if user.role == "employee" and sheet.applicant_id != user.id:
        return error("无权修改该单据", code=403)
    if sheet.status not in (ExpenseSheet.STATUS_DRAFT, ExpenseSheet.STATUS_REJECTED):
        return error("单据当前状态不可修改")

    data = request.get_json(silent=True) or {}
    if "title" in data:
        sheet.title = data["title"]
    if "reason" in data:
        sheet.reason = data["reason"]

    # 全量替换明细
    if "items" in data:
        for old in sheet.items.all():
            db.session.delete(old)
        for it in data["items"]:
            item = ExpenseItem(
                sheet_id=sheet.id,
                category_id=it["category_id"],
                amount=it["amount"],
                occur_date=datetime.date.fromisoformat(it["occur_date"]),
                description=it.get("description"),
                invoice_no=it.get("invoice_no"),
                remark=it.get("remark"),
            )
            db.session.add(item)
        _recalc_total(sheet)
    db.session.commit()
    return success(sheet.to_dict(with_items=True), message="更新成功")


@expense_bp.route("/<int:sheet_id>", methods=["DELETE"])
@role_required()
def delete_sheet(sheet_id):
    sheet = ExpenseSheet.query.get(sheet_id)
    if sheet is None:
        return error("报销单不存在")
    user = get_current_user()
    if user.role == "employee" and sheet.applicant_id != user.id:
        return error("无权删除该单据", code=403)
    if sheet.status not in (ExpenseSheet.STATUS_DRAFT, ExpenseSheet.STATUS_REJECTED):
        return error("单据当前状态不可删除")
    db.session.delete(sheet)
    db.session.commit()
    return success(message="删除成功")


@expense_bp.route("/<int:sheet_id>/submit", methods=["POST"])
@role_required()
def submit_sheet(sheet_id):
    """提交报销单进入审批流程"""
    sheet = ExpenseSheet.query.get(sheet_id)
    if sheet is None:
        return error("报销单不存在")
    user = get_current_user()
    if sheet.applicant_id != user.id:
        return error("只能提交自己的单据")
    if not sheet.items.count():
        return error("请至少添加一条报销明细")
    if sheet.status not in (ExpenseSheet.STATUS_DRAFT, ExpenseSheet.STATUS_REJECTED):
        return error("单据已提交，无法重复提交")

    from app.models import ApprovalRecord, ApprovalFlow

    # 匹配审批流（按金额/部门动态路由）
    flow = ApprovalFlow.match_flow(
        float(sheet.total_amount), sheet.department_id
    )
    if flow is None:
        return error("未找到匹配的审批流，请联系管理员配置")
    sheet.flow_id = flow.id
    sheet.status = ExpenseSheet.STATUS_PENDING
    sheet.current_node = 1  # 从第一个节点开始
    rec = ApprovalRecord(
        sheet_id=sheet.id,
        approver_id=user.id,
        node=0,
        action=ApprovalRecord.ACTION_SUBMIT,
        before_status=ExpenseSheet.STATUS_DRAFT,
        after_status=ExpenseSheet.STATUS_PENDING,
        comment=f"提交报销（匹配审批流：{flow.name}）",
    )
    db.session.add(rec)
    db.session.commit()
    return success(sheet.to_dict(), message="提交成功，等待审批")
