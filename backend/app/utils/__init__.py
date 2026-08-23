"""
统一 API 响应工具
"""
from flask import jsonify


def success(data=None, message="ok"):
    return jsonify({"code": 0, "message": message, "data": data})


def error(message="error", code=1, http_status=400):
    return jsonify({"code": code, "message": message, "data": None}), http_status
