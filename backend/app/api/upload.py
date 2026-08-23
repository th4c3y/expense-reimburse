"""
附件上传与发票 OCR 接口
上传发票图片到本地 uploads 目录，并触发 OCR 识别，返回识别金额/发票号供前端回填。
"""
import os
import time
import uuid

from flask import request, send_from_directory, current_app
from werkzeug.utils import secure_filename

from app import db
from app.models import Attachment
from app.utils import error, success
from app.utils.auth import role_required, get_current_user
from app.utils.ocr import ocr_image

upload_bp = __import__("flask").Blueprint("upload", __name__)

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".pdf", ".webp"}
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")


def _save_file(file, sheet_id, item_id):
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXT:
        return None, "不支持的文件类型"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    stored = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(UPLOAD_DIR, stored)
    file.save(save_path)

    att = Attachment(
        item_id=item_id,
        sheet_id=sheet_id,
        original_name=filename,
        stored_name=stored,
        file_path=f"/api/upload/file/{stored}",
        file_size=os.path.getsize(save_path),
        mime_type=file.mimetype,
        ocr_status=0,
    )
    db.session.add(att)
    db.session.flush()

    # 触发 OCR
    try:
        ocr_result = ocr_image(save_path, filename)
        att.ocr_text = ocr_result.get("ocr_text")
        att.ocr_amount = ocr_result.get("amount")
        att.ocr_invoice_no = ocr_result.get("invoice_no")
        att.ocr_status = ocr_result.get("status", 0)
    except Exception as e:
        att.ocr_status = 2
        att.ocr_text = f"OCR 失败: {e}"
    db.session.commit()
    return att, None


@upload_bp.route("/file", methods=["POST"])
@role_required()
def upload_file():
    """上传附件，可选关联 sheet_id / item_id"""
    if "file" not in request.files:
        return error("未找到上传文件")
    file = request.files["file"]
    if file.filename == "":
        return error("文件名为空")
    sheet_id = request.form.get("sheet_id")
    item_id = request.form.get("item_id")
    att, err = _save_file(file, sheet_id, item_id)
    if err:
        return error(err)
    return success(att.to_dict(), message="上传成功")


@upload_bp.route("/file/<stored>", methods=["GET"])
def get_file(stored):
    """访问上传的文件"""
    return send_from_directory(UPLOAD_DIR, stored)


@upload_bp.route("/list", methods=["GET"])
@role_required()
def list_attachments():
    """按 sheet_id 或 item_id 查询附件列表"""
    sheet_id = request.args.get("sheet_id")
    item_id = request.args.get("item_id")
    query = Attachment.query
    if sheet_id:
        query = query.filter_by(sheet_id=sheet_id)
    if item_id:
        query = query.filter_by(item_id=item_id)
    items = query.order_by(Attachment.id.desc()).all()
    return success([a.to_dict() for a in items])


@upload_bp.route("/<int:att_id>", methods=["DELETE"])
@role_required()
def delete_attachment(att_id):
    att = Attachment.query.get(att_id)
    if att is None:
        return error("附件不存在")
    # 删除本地文件
    try:
        if att.stored_name:
            p = os.path.join(UPLOAD_DIR, att.stored_name)
            if os.path.exists(p):
                os.remove(p)
    except Exception:
        pass
    db.session.delete(att)
    db.session.commit()
    return success(message="删除成功")
