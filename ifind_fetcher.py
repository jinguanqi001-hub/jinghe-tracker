# -*- coding: utf-8 -*-
"""同花顺 iFinD 官方接口适配（需账号，可选）"""

import json
import os
import ssl
import urllib.request
from datetime import datetime, timedelta

from ths_config import IFIND

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


def _ifind_configured():
    user = os.environ.get("IFIND_USER") or IFIND.get("username")
    token = os.environ.get("IFIND_TOKEN") or IFIND.get("access_token")
    return bool(IFIND.get("enabled") and (token or user))


def _try_ifind_sdk_login():
    try:
        from iFinDPy import THS_iFinDLogin
    except ImportError:
        return False, "未安装 iFinDPy（需 iFinD 终端 SDK）"
    user = os.environ.get("IFIND_USER") or IFIND["username"]
    pwd = os.environ.get("IFIND_PASS") or IFIND["password"]
    if not user or not pwd:
        return False, "请配置 IFIND_USER / IFIND_PASS"
    ret = THS_iFinDLogin(user, pwd)
    if ret not in (0, -201):
        return False, "iFinD 登录失败，错误码 {}".format(ret)
    return True, "ok"


def fetch_daily_klines(days=120):
    ok, msg = _try_ifind_sdk_login()
    if not ok:
        raise RuntimeError(msg)
    from iFinDPy import THS_HistoryQuotes

    code = IFIND["stock_code"]
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=int(days * 1.6))).strftime("%Y-%m-%d")
    res = THS_HistoryQuotes(
        code,
        "open,high,low,close,volume,amount,turnoverRatio",
        "Period:D,Fill:Previous,PriceType:1",
        start,
        end,
    )
    if res.errorcode != 0:
        raise RuntimeError("iFinD 历史行情: {}".format(res.errmsg))
    rows = []
    for _, r in res.data.iterrows():
        rows.append(
            {
                "date": str(r.get("time", ""))[:10],
                "open": float(r["open"]),
                "high": float(r["high"]),
                "low": float(r["low"]),
                "close": float(r["close"]),
                "volume": int(float(r.get("volume", 0)) // 100),
                "amount": float(r.get("amount", 0)),
                "turnover_pct": float(r.get("turnoverRatio", 0) or 0),
                "change_pct": 0.0,
                "change": 0.0,
                "amplitude_pct": 0.0,
                "source": "ifind",
            }
        )
    return rows[-days:] if days else rows


def fetch_realtime():
    ok, msg = _try_ifind_sdk_login()
    if not ok:
        raise RuntimeError(msg)
    from iFinDPy import THS_RealtimeQuotes

    code = IFIND["stock_code"]
    res = THS_RealtimeQuotes(code, "open;high;low;latest;volume;amount;changeRatio;turnoverRatio")
    if res.errorcode != 0:
        raise RuntimeError("iFinD 实时行情: {}".format(res.errmsg))
    d = res.data.iloc[0]
    return {
        "code": "688249",
        "name": "晶合集成",
        "price": float(d.get("latest", 0)),
        "open": float(d.get("open", 0)),
        "high": float(d.get("high", 0)),
        "low": float(d.get("low", 0)),
        "pre_close": None,
        "volume": int(float(d.get("volume", 0)) // 100),
        "amount": float(d.get("amount", 0)),
        "turnover_pct": float(d.get("turnoverRatio", 0) or 0),
        "change_pct": float(d.get("changeRatio", 0) or 0),
        "source": "ifind",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def is_available():
    return _ifind_configured()
