# -*- coding: utf-8 -*-
"""同花顺问财 (i问财) 联动 — 可选 cookie，无 cookie 时生成链接"""

import json
import os
import ssl
import urllib.parse
import urllib.request

from ths_config import THS_PUBLIC

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"

# 晶合集成预设问句（可在 ths_config 或环境变量覆盖）
PRESET_QUERIES = {
    "fundamental": "688249 市盈率;市净率;总市值;流通市值;所属概念",
    "flow": "688249 主力资金;北向资金;融资余额",
    "industry": "688249 所属行业;晶圆代工;同行业",
    "risk": "688249 限售解禁;股东减持;业绩预警",
}

IWENCAI_API = "https://www.iwencai.com/customized/chart/get-robot-data"


def _get_cookie():
    return os.environ.get("IWENCAI_COOKIE", "").strip()


def build_url(query):
    return "https://www.iwencai.com/unifiedwap/result?w=" + urllib.parse.quote(query)


def _fetch_robot(query, cookie):
    payload = {
        "source": "Ths_iwencai_xuangu",
        "version": "2.0",
        "query_area": "",
        "add_info": json.dumps(
            {"urp": {"scene": 1, "company": 1, "business": 1}, "contentType": "json", "searchInfo": True}
        ),
        "question": query,
        "perpage": 50,
        "page": 1,
        "secondary_intent": "stock",
        "log_info": json.dumps({"input_type": "click"}),
    }
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "User-Agent": UA,
        "Content-Type": "application/json",
        "Referer": "https://www.iwencai.com/unifiedwap/result",
        "Cookie": cookie,
    }
    req = urllib.request.Request(IWENCAI_API, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=20, context=SSL_CTX) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _extract_fields(data):
    """从问财 JSON 提取 688249 相关字段"""
    fields = {}
    try:
        answer = (data.get("data") or {}).get("answer") or []
        for block in answer:
            for comp in block.get("txt", []) if isinstance(block.get("txt"), list) else []:
                pass
            components = block.get("components") or []
            for comp in components:
                cid = comp.get("cid")
                if cid != 6836372:  # 表格组件类型可能变化
                    continue
                table = (comp.get("data") or {}).get("datas") or []
                for row in table:
                    code = str(row.get("code") or row.get("股票代码") or "")
                    if "688249" not in code:
                        continue
                    for k, v in row.items():
                        if v is not None and str(v).strip():
                            fields[k] = v
    except Exception:
        pass
    return fields


def query(preset="fundamental", custom_query=None):
    """
    查询问财。返回 dict:
      - ok: bool
      - query: 问句
      - fields: 提取的字段 (有 cookie 且成功时)
      - url: 浏览器链接
      - message: 提示信息
    """
    q = custom_query or PRESET_QUERIES.get(preset) or PRESET_QUERIES["fundamental"]
    url = build_url(q)
    cookie = _get_cookie()

    if not cookie:
        return {
            "ok": False,
            "query": q,
            "fields": {},
            "url": url,
            "message": "未设置 IWENCAI_COOKIE，请浏览器登录 iwencai.com 后复制 Cookie，或使用 --open-iwencai 打开链接",
        }

    try:
        raw = _fetch_robot(q, cookie)
        if raw.get("code") != 0 or (raw.get("data") or {}).get("captcha_url"):
            return {
                "ok": False,
                "query": q,
                "fields": {},
                "url": url,
                "message": "问财需要验证码或 Cookie 失效，请更新 IWENCAI_COOKIE",
            }
        fields = _extract_fields(raw)
        if not fields:
            # 尝试 pywencai 备选
            fields = _try_pywencai(q, cookie)
        return {
            "ok": bool(fields),
            "query": q,
            "fields": fields,
            "url": url,
            "message": "问财查询成功" if fields else "已连接问财但未解析到688249字段，请用 --open-iwencai 查看",
        }
    except Exception as e:
        return {
            "ok": False,
            "query": q,
            "fields": {},
            "url": url,
            "message": "问财请求失败: {}".format(e),
        }


def _try_pywencai(q, cookie):
    try:
        import pywencai
        df = pywencai.get(query=q, cookie=cookie)
        if df is None or df.empty:
            return {}
        row = df[df.iloc[:, 0].astype(str).str.contains("688249", na=False)]
        if row.empty:
            row = df.head(1)
        return row.iloc[0].to_dict()
    except ImportError:
        return {}
    except Exception:
        return {}


def query_all_presets():
    results = {}
    for name in PRESET_QUERIES:
        results[name] = query(preset=name)
    return results


def open_iwencai(query=None, preset="fundamental"):
    import webbrowser
    q = query or PRESET_QUERIES.get(preset, PRESET_QUERIES["fundamental"])
    url = build_url(q)
    webbrowser.open(url)
    return url
