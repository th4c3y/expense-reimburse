"""
应用配置
数据库使用外部已存在的空白 MariaDB。
修改下方 SQLALCHEMY_DATABASE_URI 以匹配你的数据库环境。
"""
import os


class Config:
    # ===== 基础配置 =====
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key-in-production")

    # ===== MariaDB 连接配置 =====
    # 格式: mysql+pymysql://<user>:<password>@<host>:<port>/<database>
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "rootpassword")
    DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_NAME = os.environ.get("DB_NAME", "expense_db")

    # 演示/测试场景可设置 USE_SQLITE=1  fallback 到 SQLite，无需外部 MariaDB。
    if os.environ.get("USE_SQLITE") in ("1", "true", "yes"):
        DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database"))
        os.makedirs(DB_DIR, exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(DB_DIR, 'expense_demo.db')}"
    else:
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
            f"?charset=utf8mb4"
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # ===== JWT 配置 =====
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-jwt-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60 * 24 * 7  # 7 天
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # ===== CORS 配置 =====
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
