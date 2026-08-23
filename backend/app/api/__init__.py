"""
蓝图注册中心
"""
from app.api.auth import auth_bp
from app.api.user import user_bp
from app.api.department import dept_bp
from app.api.category import category_bp
from app.api.expense import expense_bp
from app.api.approval import approval_bp
from app.api.statistics import stats_bp
from app.api.flow import flow_bp
from app.api.upload import upload_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(user_bp, url_prefix="/api/users")
    app.register_blueprint(dept_bp, url_prefix="/api/departments")
    app.register_blueprint(category_bp, url_prefix="/api/categories")
    app.register_blueprint(expense_bp, url_prefix="/api/expenses")
    app.register_blueprint(approval_bp, url_prefix="/api/approvals")
    app.register_blueprint(stats_bp, url_prefix="/api/stats")
    app.register_blueprint(flow_bp, url_prefix="/api/flows")
    app.register_blueprint(upload_bp, url_prefix="/api/upload")
