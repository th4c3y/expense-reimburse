"""
数据库初始化脚本
在公司提供的空白 MariaDB 数据库中创建所有表并写入初始数据。

用法:
    cd backend
    python init_db.py

环境变量（或直接在 config.py 修改）:
    DB_USER / DB_PASSWORD / DB_HOST / DB_PORT / DB_NAME
"""
import os

from app import create_app, db
from app.models import (
    User,
    Department,
    ExpenseCategory,
    ExpenseSheet,
    ExpenseItem,
    ApprovalFlow,
    ApprovalNode,
)


def seed():
    # 部门
    dev = Department.query.filter_by(code="RD").first()
    hr = Department.query.filter_by(code="HR").first()
    fin = Department.query.filter_by(code="FIN").first()
    if not dev:
        dev = Department(name="研发部", code="RD", description="研发与技术团队")
        hr = Department(name="人事行政部", code="HR", description="人事与行政")
        fin = Department(name="财务部", code="FIN", description="财务与资金")
        db.session.add_all([dev, hr, fin])
        db.session.commit()
        print("已创建部门")

    # 报销类别
    if ExpenseCategory.query.count() == 0:
        cats = [
            ("交通费", "TRAFFIC", "打车、地铁、高铁等"),
            ("餐饮招待", "MEAL", "商务宴请、工作餐"),
            ("差旅住宿", "HOTEL", "酒店住宿"),
            ("办公用品", "OFFICE", "文具、耗材"),
            ("通讯费", "COMM", "手机话费"),
            ("其他", "OTHER", "其他费用"),
        ]
        for name, code, desc in cats:
            db.session.add(ExpenseCategory(name=name, code=code, description=desc))
        db.session.commit()
        print("已创建报销类别")

    # 用户（默认密码 123456）
    if User.query.count() == 0:
        admin = User(username="admin", real_name="系统管理员",
                     role="admin", department_id=None)
        admin.password = "123456"
        manager = User(username="manager", real_name="张经理",
                       role="manager", department_id=dev.id,
                       approval_limit=5000)
        manager.password = "123456"
        finance = User(username="finance", real_name="李财务",
                       role="finance", department_id=fin.id)
        finance.password = "123456"
        emp = User(username="employee", real_name="王员工",
                   role="employee", department_id=dev.id)
        emp.password = "123456"
        db.session.add_all([admin, manager, finance, emp])
        db.session.commit()
        print("已创建示例用户")

    # 审批流（可配置多级审批种子数据）
    if ApprovalFlow.query.count() == 0:
        # 1) 默认流：部门经理 -> 财务
        default_flow = ApprovalFlow(
            name="标准审批流", description="默认：部门经理→财务",
            priority=0, min_amount=0, max_amount=None,
            department_scope="", is_default=1, status=1
        )
        db.session.add(default_flow)
        db.session.flush()
        db.session.add_all([
            ApprovalNode(flow_id=default_flow.id, order_no=1, name="部门经理审批",
                         approver_type="dept_manager", approver_value=None),
            ApprovalNode(flow_id=default_flow.id, order_no=2, name="财务审批",
                         approver_type="role", approver_value="finance"),
        ])

        # 2) 大额流：部门经理 -> 财务 -> 总经理（金额 >= 10000）
        big_flow = ApprovalFlow(
            name="大额审批流", description="金额>=10000：部门经理→财务→总经理",
            priority=10, min_amount=10000, max_amount=None,
            department_scope="", is_default=0, status=1
        )
        db.session.add(big_flow)
        db.session.flush()
        db.session.add_all([
            ApprovalNode(flow_id=big_flow.id, order_no=1, name="部门经理审批",
                         approver_type="dept_manager", approver_value=None),
            ApprovalNode(flow_id=big_flow.id, order_no=2, name="财务审批",
                         approver_type="role", approver_value="finance"),
            ApprovalNode(flow_id=big_flow.id, order_no=3, name="总经理审批",
                         approver_type="role", approver_value="admin"),
        ])
        db.session.commit()
        print("已创建审批流（标准流 + 大额流）")


def main():
    app = create_app("default")
    with app.app_context():
        print(f"连接数据库: {app.config['SQLALCHEMY_DATABASE_URI']}")
        try:
            db.create_all()
            print("数据表创建完成")
        except Exception as e:
            print(f"建表失败: {e}")
            raise
        seed()
        # 确保上传目录存在
        upload_dir = os.path.join(os.path.dirname(__file__), "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        print("初始化完成。默认账号: admin / manager / finance / employee，密码均为 123456")


if __name__ == "__main__":
    main()
