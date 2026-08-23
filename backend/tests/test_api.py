"""
核心业务逻辑测试
"""
from app.utils.ocr import _regex_parse


def _login(client, username):
    r = client.post("/api/auth/login", json={"username": username, "password": "123456"})
    assert r.status_code == 200
    return r.get_json()["data"]["token"]


def test_login_success(client):
    r = client.post("/api/auth/login", json={"username": "admin", "password": "123456"})
    assert r.status_code == 200
    assert r.get_json()["data"]["token"]


def test_login_wrong_password(client):
    r = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert r.get_json()["code"] == 401


def test_me_requires_token(client):
    r = client.get("/api/auth/me")
    # 未携带 token，JWT 拦截
    assert r.status_code in (401, 422)


def test_flow_match_small_amount(client, app):
    from app.models import ApprovalFlow
    dept = 1
    flow = ApprovalFlow.match_flow(500, dept)
    assert flow is not None
    assert flow.name == "标准"
    # 标准流只有 2 个节点
    assert flow.nodes.count() == 2


def test_flow_match_big_amount(client, app):
    from app.models import ApprovalFlow
    flow = ApprovalFlow.match_flow(20000, 1)
    assert flow.name == "大额"
    assert flow.nodes.count() == 3


def test_expense_submit_and_multi_approve(client, app):
    """提交报销单 -> 经理审批 -> 财务审批 -> 通过（两级）"""
    token = _login(client, "employee")
    h = {"Authorization": f"Bearer {token}"}
    # 创建报销单
    r = client.post("/api/expenses", json={
        "title": "测试报销",
        "items": [{"category_id": 1, "amount": 800, "occur_date": "2026-08-20"}]
    }, headers=h)
    assert r.status_code == 200
    sheet_id = r.get_json()["data"]["id"]

    # 提交
    r = client.post(f"/api/expenses/{sheet_id}/submit", headers=h)
    assert r.status_code == 200
    assert r.get_json()["data"]["status"] == "pending"
    assert r.get_json()["data"]["flow_id"] == 1  # 标准流

    # 经理审批
    mgr_token = _login(client, "manager")
    mh = {"Authorization": f"Bearer {mgr_token}"}
    r = client.post(f"/api/approvals/{sheet_id}/approve", json={"comment": "同意"}, headers=mh)
    assert r.status_code == 200
    assert r.get_json()["data"]["status"] == "pending"  # 还在财务节点

    # 财务审批
    fin_token = _login(client, "finance")
    fh = {"Authorization": f"Bearer {fin_token}"}
    r = client.post(f"/api/approvals/{sheet_id}/approve", json={"comment": "ok"}, headers=fh)
    assert r.status_code == 200
    assert r.get_json()["data"]["status"] == "approved"

    # 财务付款
    r = client.post(f"/api/approvals/{sheet_id}/pay", headers=fh)
    assert r.status_code == 200
    assert r.get_json()["data"]["status"] == "paid"


def test_expense_reject(client, app):
    token = _login(client, "employee")
    h = {"Authorization": f"Bearer {token}"}
    r = client.post("/api/expenses", json={
        "title": "驳回测试",
        "items": [{"category_id": 1, "amount": 300, "occur_date": "2026-08-20"}]
    }, headers=h)
    sheet_id = r.get_json()["data"]["id"]
    client.post(f"/api/expenses/{sheet_id}/submit", headers=h)

    mgr_token = _login(client, "manager")
    mh = {"Authorization": f"Bearer {mgr_token}"}
    r = client.post(f"/api/approvals/{sheet_id}/reject", json={"comment": "金额不符"}, headers=mh)
    assert r.status_code == 200
    assert r.get_json()["data"]["status"] == "rejected"


def test_ocr_regex_parse():
    text = "发票号码: 8812345678\n金额: ¥1234.56"
    amount, invoice = _regex_parse(text)
    assert amount == 1234.56
    assert invoice == "8812345678"


def test_ocr_regex_no_match():
    amount, invoice = _regex_parse("这是一张没有金额的发票")
    assert amount is None
