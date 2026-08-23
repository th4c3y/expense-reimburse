"""
统计报表接口
"""
from datetime import datetime

from sqlalchemy import func

from app import db
from app.models import ExpenseSheet, ExpenseItem, ExpenseCategory, Department
from app.utils import success
from app.utils.auth import role_required

stats_bp = __import__("flask").Blueprint("stats", __name__)


@stats_bp.route("/overview", methods=["GET"])
@role_required("admin", "finance", "manager")
def overview():
    """概览卡片数据"""
    total = ExpenseSheet.query.count()
    pending = ExpenseSheet.query.filter_by(status=ExpenseSheet.STATUS_PENDING).count()
    approved = ExpenseSheet.query.filter_by(
        status=ExpenseSheet.STATUS_APPROVED
    ).count()
    paid = ExpenseSheet.query.filter_by(status=ExpenseSheet.STATUS_PAID).count()
    paid_amount = (
        db.session.query(func.coalesce(func.sum(ExpenseSheet.total_amount), 0))
        .filter(ExpenseSheet.status == ExpenseSheet.STATUS_PAID)
        .scalar()
    )
    return success(
        {
            "total_sheets": total,
            "pending": pending,
            "approved": approved,
            "paid": paid,
            "paid_amount": float(paid_amount),
        }
    )


@stats_bp.route("/by-category", methods=["GET"])
@role_required("admin", "finance", "manager")
def by_category():
    """各报销类别金额分布（仅统计已通过/已付款）"""
    rows = (
        db.session.query(
            ExpenseCategory.name,
            func.coalesce(func.sum(ExpenseItem.amount), 0),
        )
        .join(ExpenseItem, ExpenseItem.category_id == ExpenseCategory.id)
        .join(ExpenseSheet, ExpenseSheet.id == ExpenseItem.sheet_id)
        .filter(
            ExpenseSheet.status.in_(
                [ExpenseSheet.STATUS_APPROVED, ExpenseSheet.STATUS_PAID]
            )
        )
        .group_by(ExpenseCategory.name)
        .all()
    )
    return success(
        [{"name": r[0], "amount": float(r[1])} for r in rows]
    )


@stats_bp.route("/by-department", methods=["GET"])
@role_required("admin", "finance", "manager")
def by_department():
    """各部门报销金额"""
    rows = (
        db.session.query(
            Department.name,
            func.coalesce(func.sum(ExpenseSheet.total_amount), 0),
        )
        .join(ExpenseSheet, ExpenseSheet.department_id == Department.id)
        .filter(
            ExpenseSheet.status.in_(
                [ExpenseSheet.STATUS_APPROVED, ExpenseSheet.STATUS_PAID]
            )
        )
        .group_by(Department.name)
        .all()
    )
    return success(
        [{"name": r[0] or "未分配", "amount": float(r[1])} for r in rows]
    )


@stats_bp.route("/trend", methods=["GET"])
@role_required("admin", "finance", "manager")
def trend():
    """近 6 个月报销金额趋势"""
    now = datetime.now()
    result = []
    for i in range(5, -1, -1):
        month = (now.month - i - 1) % 12 + 1
        year = now.year - ((now.month - i - 1) < 0)
        month_str = f"{year}-{str(month).zfill(2)}"
        amount = (
            db.session.query(func.coalesce(func.sum(ExpenseSheet.total_amount), 0))
            .filter(
                func.date_format(ExpenseSheet.created_at, "%Y-%m") == month_str,
                ExpenseSheet.status.in_(
                    [ExpenseSheet.STATUS_APPROVED, ExpenseSheet.STATUS_PAID]
                ),
            )
            .scalar()
        )
        result.append({"month": month_str, "amount": float(amount)})
    return success(result)
