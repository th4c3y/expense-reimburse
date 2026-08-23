"""
pytest 配置：使用 SQLite 内存库测试核心业务逻辑（无需真实 MariaDB）。
运行:
    cd backend
    pip install pytest
    pytest -q
"""
import pytest
from app import create_app, db as _db
from app.models import (
    User, Department, ExpenseCategory, ExpenseSheet, ExpenseItem,
    ApprovalFlow, ApprovalNode,
)


@pytest.fixture
def app():
    # 使用 SQLite 内存库隔离测试，不依赖外部 MariaDB。
    # 必须在 init_app 之前覆盖 DATABASE_URI，因此通过 config_override 传入。
    app = create_app(
        "default",
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            # 关闭 JWT 的 Cookie 强制要求，便于测试
            "JWT_TOKEN_LOCATION": ["headers"],
        },
    )
    with app.app_context():
        _db.create_all()
        _seed_test_data()
        yield app
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _seed_test_data():
    dept = Department(name="研发部", code="RD")
    fin = Department(name="财务部", code="FIN")
    _db.session.add_all([dept, fin])
    _db.session.commit()

    u_admin = User(username="admin", real_name="管理员", role="admin")
    u_admin.password = "123456"
    u_mgr = User(username="manager", real_name="经理", role="manager", department_id=dept.id)
    u_mgr.password = "123456"
    u_fin = User(username="finance", real_name="财务", role="finance", department_id=fin.id)
    u_fin.password = "123456"
    u_emp = User(username="employee", real_name="员工", role="employee", department_id=dept.id)
    u_emp.password = "123456"
    _db.session.add_all([u_admin, u_mgr, u_fin, u_emp])
    _db.session.commit()
    # 设置研发部负责人为 manager（dept_manager 节点需用）
    dept.manager_id = u_mgr.id
    _db.session.commit()

    cat = ExpenseCategory(name="餐饮", code="MEAL")
    _db.session.add(cat)
    _db.session.commit()

    # 标准流：部门经理 -> 财务
    flow = ApprovalFlow(name="标准", is_default=1, min_amount=0)
    _db.session.add(flow)
    _db.session.flush()
    _db.session.add_all([
        ApprovalNode(flow_id=flow.id, order_no=1, name="经理", approver_type="dept_manager"),
        ApprovalNode(flow_id=flow.id, order_no=2, name="财务", approver_type="role", approver_value="finance"),
    ])
    # 大额流：>=10000 额外加总经理
    big = ApprovalFlow(name="大额", priority=10, min_amount=10000)
    _db.session.add(big)
    _db.session.flush()
    _db.session.add_all([
        ApprovalNode(flow_id=big.id, order_no=1, name="经理", approver_type="dept_manager"),
        ApprovalNode(flow_id=big.id, order_no=2, name="财务", approver_type="role", approver_value="finance"),
        ApprovalNode(flow_id=big.id, order_no=3, name="总经理", approver_type="role", approver_value="admin"),
    ])
    _db.session.commit()
