"""
Flask 应用工厂
"""
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

from config import config_map

# 全局扩展对象（在 create_app 中初始化）
db = SQLAlchemy()
jwt = JWTManager()


def create_app(config_name: str = "default", config_override: dict = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, config_map["default"]))
    if config_override:
        app.config.update(config_override)

    # 初始化扩展
    db.init_app(app)
    jwt.init_app(app)
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )

    # 注册蓝图
    from app.api import register_blueprints
    register_blueprints(app)

    # 健康检查
    @app.route("/api/health")
    def health():
        return {"code": 0, "message": "ok", "data": {"service": "expense-backend"}}

    return app
