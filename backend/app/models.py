"""
数据库模型定义
公司费用报销系统
"""
from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from app import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


# ===================== 部门 =====================
class Department(db.Model, TimestampMixin):
    __tablename__ = "department"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False, comment="部门名称")
    code = db.Column(db.String(32), unique=True, nullable=False, comment="部门编码")
    manager_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    description = db.Column(db.String(255))

    # 部门负责人（一对一，通过 manager_id）
    manager = db.relationship(
        "User",
        foreign_keys=[manager_id],
        primaryjoin="Department.manager_id == User.id",
        uselist=False,
        lazy="joined",
    )
    # 本部门员工（通过 User.department_id 反向）
    users = db.relationship(
        "User",
        primaryjoin="Department.id == User.department_id",
        foreign_keys="User.department_id",
        backref="department",
        lazy="dynamic",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "manager_id": self.manager_id,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ===================== 用户 =====================
class User(db.Model, TimestampMixin):
    __tablename__ = "user"

    ROLE_ADMIN = "admin"        # 系统管理员
    ROLE_MANAGER = "manager"    # 部门经理
    ROLE_FINANCE = "finance"    # 财务
    ROLE_EMPLOYEE = "employee"  # 普通员工

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, comment="登录名")
    password_hash = db.Column(db.String(255), nullable=False)
    real_name = db.Column(db.String(64), nullable=False, comment="真实姓名")
    email = db.Column(db.String(128))
    phone = db.Column(db.String(32))
    department_id = db.Column(
        db.Integer, db.ForeignKey("department.id"), nullable=True
    )
    role = db.Column(db.String(32), default=ROLE_EMPLOYEE, nullable=False)
    status = db.Column(db.Integer, default=1, comment="1启用 0禁用")  # 1启用 0禁用
    approval_limit = db.Column(
        db.Numeric(12, 2), default=0, comment="审批额度上限"
    )

    expense_sheets = db.relationship(
        "ExpenseSheet", backref="applicant", lazy="dynamic"
    )

    @property
    def password(self):
        raise AttributeError("password is not readable")

    @password.setter
    def password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def verify_password(self, raw):
        return check_password_hash(self.password_hash, raw)

    def to_dict(self, with_sensitive=False):
        d = {
            "id": self.id,
            "username": self.username,
            "real_name": self.real_name,
            "email": self.email,
            "phone": self.phone,
            "department_id": self.department_id,
            "role": self.role,
            "status": self.status,
            "approval_limit": (
                float(self.approval_limit) if self.approval_limit else 0
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if with_sensitive:
            d["password_hash"] = self.password_hash
        return d


# ===================== 报销类别 =====================
class ExpenseCategory(db.Model, TimestampMixin):
    __tablename__ = "expense_category"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, comment="类别名称")
    code = db.Column(db.String(32), unique=True, nullable=False)
    description = db.Column(db.String(255))
    status = db.Column(db.Integer, default=1)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "status": self.status,
        }


# ===================== 报销单 =====================
class ExpenseSheet(db.Model, TimestampMixin):
    __tablename__ = "expense_sheet"

    STATUS_DRAFT = "draft"            # 草稿
    STATUS_PENDING = "pending"        # 审批中
    STATUS_APPROVED = "approved"      # 审批通过
    STATUS_REJECTED = "rejected"      # 驳回
    STATUS_PAID = "paid"              # 已付款

    id = db.Column(db.Integer, primary_key=True)
    sheet_no = db.Column(
        db.String(32), unique=True, nullable=False, comment="单据编号"
    )
    applicant_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False
    )
    department_id = db.Column(
        db.Integer, db.ForeignKey("department.id"), nullable=True
    )
    title = db.Column(db.String(128), nullable=False, comment="报销标题")
    reason = db.Column(db.Text, comment="报销事由")
    total_amount = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    status = db.Column(db.String(32), default=STATUS_DRAFT, nullable=False)
    flow_id = db.Column(
        db.Integer, db.ForeignKey("approval_flow.id"), nullable=True,
        comment="匹配到的审批流ID"
    )
    current_node = db.Column(db.Integer, default=1, comment="当前审批节点序号(order_no)")
    reject_reason = db.Column(db.Text)
    paid_at = db.Column(db.DateTime)
    approved_at = db.Column(db.DateTime)

    items = db.relationship(
        "ExpenseItem", backref="sheet", lazy="dynamic", cascade="all, delete-orphan"
    )
    approvals = db.relationship(
        "ApprovalRecord",
        backref="sheet",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    attachments = db.relationship(
        "Attachment", backref="sheet", lazy="dynamic", cascade="all, delete-orphan"
    )

    def to_dict(self, with_items=False):
        d = {
            "id": self.id,
            "sheet_no": self.sheet_no,
            "applicant_id": self.applicant_id,
            "department_id": self.department_id,
            "title": self.title,
            "reason": self.reason,
            "total_amount": float(self.total_amount) if self.total_amount else 0,
            "status": self.status,
            "flow_id": self.flow_id,
            "current_node": self.current_node,
            "reject_reason": self.reject_reason,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "approved_at": (
                self.approved_at.isoformat() if self.approved_at else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if with_items:
            d["items"] = [i.to_dict() for i in self.items.all()]
        return d

    def get_current_node(self):
        """返回当前待审批的 ApprovalNode，最终通过返回 None"""
        if self.flow_id is None:
            return None
        flow = ApprovalFlow.query.get(self.flow_id)
        if not flow:
            return None
        return flow.nodes.filter_by(order_no=self.current_node).first()

    def resolve_approvers(self, node):
        """根据节点配置解析实际审批人用户列表"""
        from app.models import User, Department

        approvers = []
        if node.approver_type == "role":
            approvers = User.query.filter_by(
                role=node.approver_value, status=1
            ).all()
        elif node.approver_type == "user":
            u = User.query.get(int(node.approver_value)) if node.approver_value else None
            if u:
                approvers = [u]
        elif node.approver_type == "dept_manager":
            if self.department_id:
                dept = Department.query.get(self.department_id)
                if dept and dept.manager_id:
                    u = User.query.get(dept.manager_id)
                    if u:
                        approvers = [u]
            # 回退：部门负责人未配置时，按 manager 角色审批，避免流程卡死
            if not approvers:
                approvers = User.query.filter_by(role="manager", status=1).all()
        elif node.approver_type == "finance_director":
            # 映射为 finance 角色（演示用）
            approvers = User.query.filter_by(role="finance", status=1).all()
        return approvers


# ===================== 报销明细 =====================
class ExpenseItem(db.Model, TimestampMixin):
    __tablename__ = "expense_item"

    id = db.Column(db.Integer, primary_key=True)
    sheet_id = db.Column(
        db.Integer, db.ForeignKey("expense_sheet.id"), nullable=False
    )
    category_id = db.Column(
        db.Integer, db.ForeignKey("expense_category.id"), nullable=False
    )
    amount = db.Column(db.Numeric(12, 2), nullable=False, comment="金额")
    occur_date = db.Column(db.Date, nullable=False, comment="发生日期")
    description = db.Column(db.String(255), comment="说明")
    invoice_no = db.Column(db.String(64), comment="发票号")
    remark = db.Column(db.String(255))

    def to_dict(self):
        return {
            "id": self.id,
            "sheet_id": self.sheet_id,
            "category_id": self.category_id,
            "amount": float(self.amount) if self.amount else 0,
            "occur_date": (
                self.occur_date.isoformat() if self.occur_date else None
            ),
            "description": self.description,
            "invoice_no": self.invoice_no,
            "remark": self.remark,
        }


# ===================== 审批记录 =====================
class ApprovalRecord(db.Model, TimestampMixin):
    __tablename__ = "approval_record"

    ACTION_SUBMIT = "submit"
    ACTION_APPROVE = "approve"
    ACTION_REJECT = "reject"
    ACTION_TRANSFER = "transfer"
    ACTION_COMMENT = "comment"

    id = db.Column(db.Integer, primary_key=True)
    sheet_id = db.Column(
        db.Integer, db.ForeignKey("expense_sheet.id"), nullable=False
    )
    approver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    node = db.Column(db.Integer, default=1, comment="审批节点")
    action = db.Column(db.String(32), nullable=False, comment="操作类型")
    comment = db.Column(db.Text, comment="审批意见")
    before_status = db.Column(db.String(32))
    after_status = db.Column(db.String(32))

    def to_dict(self):
        return {
            "id": self.id,
            "sheet_id": self.sheet_id,
            "approver_id": self.approver_id,
            "node": self.node,
            "action": self.action,
            "comment": self.comment,
            "before_status": self.before_status,
            "after_status": self.after_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ===================== 审批流配置 =====================
class ApprovalFlow(db.Model, TimestampMixin):
    """
    审批流模板。系统可配置多条流，按优先级 + 金额/部门条件匹配报销单。
    例：
      - 默认流：部门经理 -> 财务
      - 大额流（金额>=10000）：部门经理 -> 财务总监 -> 总经理
    """

    __tablename__ = "approval_flow"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, comment="审批流名称")
    description = db.Column(db.String(255))
    priority = db.Column(db.Integer, default=0, comment="优先级，数值越大越优先匹配")
    min_amount = db.Column(
        db.Numeric(12, 2), default=0, comment="适用最低金额（含）"
    )
    max_amount = db.Column(
        db.Numeric(12, 2), nullable=True, comment="适用最高金额（不含），NULL 表示无上限"
    )
    # 适用部门，逗号分隔的部门ID；空表示适用全部部门
    department_scope = db.Column(db.String(255), default="", comment="适用部门ID列表,逗号分隔")
    is_default = db.Column(db.Integer, default=0, comment="是否为默认流")
    status = db.Column(db.Integer, default=1, comment="1启用 0停用")

    nodes = db.relationship(
        "ApprovalNode",
        backref="flow",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="ApprovalNode.order_no",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "min_amount": float(self.min_amount) if self.min_amount else 0,
            "max_amount": float(self.max_amount) if self.max_amount else None,
            "department_scope": self.department_scope or "",
            "is_default": self.is_default,
            "status": self.status,
            "nodes": [n.to_dict() for n in self.nodes.all()],
        }

    @staticmethod
    def match_flow(total_amount, department_id):
        """根据金额与部门匹配最合适的审批流"""
        candidates = ApprovalFlow.query.filter_by(status=1).all()
        matched = []
        for f in candidates:
            # 金额区间
            if total_amount < (float(f.min_amount) or 0):
                continue
            if f.max_amount is not None and total_amount >= float(f.max_amount):
                continue
            # 部门范围（空表示全部）
            if f.department_scope:
                scope = [int(x) for x in f.department_scope.split(",") if x.strip()]
                if department_id not in scope:
                    continue
            matched.append(f)
        if not matched:
            # 回退到默认流
            default = ApprovalFlow.query.filter_by(is_default=1, status=1).first()
            return default
        # 优先级最高者优先
        matched.sort(key=lambda x: x.priority, reverse=True)
        return matched[0]


# ===================== 审批节点 =====================
class ApprovalNode(db.Model, TimestampMixin):
    """
    审批流中的单个节点。
    approver_type:
      - role      : 按角色审批（approver_value 为角色名，如 finance）
      - dept_manager : 部门经理审批（取报销单所属部门负责人）
      - user      : 指定用户（approver_value 为用户ID）
      - finance_director : 财务总监（可映射为指定角色）
    """

    __tablename__ = "approval_node"

    id = db.Column(db.Integer, primary_key=True)
    flow_id = db.Column(
        db.Integer, db.ForeignKey("approval_flow.id"), nullable=False
    )
    order_no = db.Column(db.Integer, default=1, nullable=False, comment="节点顺序")
    name = db.Column(db.String(64), nullable=False, comment="节点名称")
    approver_type = db.Column(db.String(32), default="role", nullable=False)
    approver_value = db.Column(db.String(64), comment="角色名/用户ID/部门ID")

    def to_dict(self):
        return {
            "id": self.id,
            "flow_id": self.flow_id,
            "order_no": self.order_no,
            "name": self.name,
            "approver_type": self.approver_type,
            "approver_value": self.approver_value,
        }


# ===================== 附件 =====================
class Attachment(db.Model, TimestampMixin):
    """报销明细关联的发票/附件"""

    __tablename__ = "attachment"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(
        db.Integer, db.ForeignKey("expense_item.id"), nullable=True
    )
    sheet_id = db.Column(
        db.Integer, db.ForeignKey("expense_sheet.id"), nullable=True
    )
    original_name = db.Column(db.String(255), comment="原文件名")
    stored_name = db.Column(db.String(255), comment="存储文件名")
    file_path = db.Column(db.String(512), comment="相对路径")
    file_size = db.Column(db.Integer, default=0)
    mime_type = db.Column(db.String(64))
    ocr_text = db.Column(db.Text, comment="OCR 识别全文")
    ocr_amount = db.Column(db.Numeric(12, 2), comment="OCR 识别金额")
    ocr_invoice_no = db.Column(db.String(64), comment="OCR 识别发票号")
    ocr_status = db.Column(db.Integer, default=0, comment="0未识别 1已识别 2识别失败")

    def to_dict(self):
        return {
            "id": self.id,
            "item_id": self.item_id,
            "sheet_id": self.sheet_id,
            "original_name": self.original_name,
            "file_path": self.file_path,
            "ocr_text": self.ocr_text,
            "ocr_amount": float(self.ocr_amount) if self.ocr_amount else None,
            "ocr_invoice_no": self.ocr_invoice_no,
            "ocr_status": self.ocr_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
