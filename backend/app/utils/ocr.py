"""
发票 OCR 识别服务
- 默认提供离线正则解析（从图片文件名/已识别文本中提取金额与发票号）
- 若配置了真实的 OCR 服务（如腾讯云 OCR / 百度 OCR），可在 ocr_with_provider 中对接

环境变量:
    OCR_PROVIDER   : none(默认,离线解析) / tencent / baidu
    OCR_SECRET_ID  : 腾讯云 SecretId
    OCR_SECRET_KEY : 腾讯云 SecretKey
"""
import os
import re


def _regex_parse(text: str):
    """从文本中用正则提取金额与发票号（兜底方案，无需外部服务）"""
    amount = None
    invoice_no = None

    # 金额：匹配 ¥1234.56 或 金额 1234.56 或 小写 1234.56
    amount_patterns = [
        r"金额[¥￥]?\s*[:：]?\s*([0-9]+[.,][0-9]{2})",
        r"[¥￥]\s*([0-9]+[.,][0-9]{2})",
        r"(?:小写|价税合计)[¥￥]?\s*[:：]?\s*([0-9]+[.,][0-9]{2})",
    ]
    for p in amount_patterns:
        m = re.search(p, text)
        if m:
            try:
                amount = float(m.group(1).replace(",", ""))
                break
            except ValueError:
                pass

    # 发票号：常见 10-20 位数字或 No开头
    inv_patterns = [
        r"发票号码\s*[:：]?\s*([0-9]{8,20})",
        r"(?:发票号|No\.?|NO\.?)\s*[:：]?\s*([0-9A-Za-z]{8,20})",
        r"\b([0-9]{20})\b",
    ]
    for p in inv_patterns:
        m = re.search(p, text)
        if m:
            invoice_no = m.group(1)
            break

    return amount, invoice_no


def ocr_image(file_path: str, original_name: str = "") -> dict:
    """
    对发票图片执行 OCR。
    返回: {"ocr_text": str, "amount": float|None, "invoice_no": str|None, "status": int}
    status: 1 已识别, 2 识别失败
    """
    provider = os.environ.get("OCR_PROVIDER", "none")

    if provider in ("tencent", "baidu"):
        result = _ocr_with_provider(provider, file_path)
    else:
        # 离线占位：没有真实图片 OCR 引擎时使用文件名启发式 + 模拟文本
        result = _offline_placeholder(file_path, original_name)

    amount, invoice_no = _regex_parse(result.get("ocr_text", ""))
    result["amount"] = amount
    result["invoice_no"] = invoice_no
    return result


def _offline_placeholder(file_path: str, original_name: str) -> dict:
    """
    离线占位实现：
    - 若上传文件名形如 invoice_1234.56_8812345678.jpg，
      可解析出金额与发票号用于演示；
    - 否则返回提示文本，由前端手动填写。
    """
    text = ""
    if original_name:
        # 尝试从文件名解析： FP_金额_发票号.后缀
        m = re.search(r"_([0-9]+[.,][0-9]{2})_([0-9]{8,20})", original_name)
        if m:
            text = f"发票号码: {m.group(2)}\n金额: ¥{m.group(1)}"
    if not text:
        text = "（离线 OCR 占位：未配置真实 OCR 服务，请在表单手工录入金额与发票号）"
    return {
        "ocr_text": text,
        "status": 1 if text.startswith("发票号码") else 0,
    }


def _ocr_with_provider(provider: str, file_path: str) -> dict:
    """
    对接真实 OCR 服务的入口（占位）。
    实际接入时取消注释并安装对应 SDK，例如腾讯云：
        pip install tencentcloud-sdk-python
    并在下方调用通用票据识别接口。
    """
    # try:
    #     from tencentcloud.common import credential
    #     from tencentcloud.ocr.v20181119 import ocr_client, models
    #     cred = credential.Credential(os.environ["OCR_SECRET_ID"],
    #                                 os.environ["OCR_SECRET_KEY"])
    #     client = ocr_client.OcrClient(cred, "ap-guangzhou")
    #     req = models.RecognizeGeneralInvoiceRequest()
    #     # 读取图片 base64 并填充 req.ImageBase64
    #     ... 省略具体实现 ...
    #     return {"ocr_text": raw_text, "status": 1}
    # except Exception as e:
    #     return {"ocr_text": f"OCR 调用失败: {e}", "status": 2}
    return {
        "ocr_text": "（未实现真实 OCR 对接，请配置 OCR_PROVIDER 与密钥并在 _ocr_with_provider 中实现）",
        "status": 2,
    }
