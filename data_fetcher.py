# -*- coding: utf-8 -*-
"""统一数据入口 — 支持同花顺 / 东方财富 / iFinD"""

import json
import os
import ssl
import urllib.parse
import urllib.request
from datetime import datetime

from config import DATA_CACHE_DIR, HISTORY_DAYS, SECID, STOCK_CODE
from ths_config import DATA_SOURCE

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _get(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _eastmoney_realtime():
    fields = "f43,f44,f45,f46,f47,f48,f57,f58,f60,f116,f117,f168,f169,f170"
    url = (
        "https://push2.eastmoney.com/api/qt/stock/get?"
        + urllib.parse.urlencode({"secid": SECID, "fields": fields, "ut": "fa5fd1943c7b386f172d6893dbfbaeb4"})
    )
    data = _get(url)
    item = data.get("data") or {}
    if not item:
        raise RuntimeError("东方财富: 无法获取实时行情")

    def px(v):
        if v is None or v == "-":
            return None
        v = float(v)
        return v / 100.0 if v > 1000 else v

    price = px(item.get("f43")) or px(item.get("f60"))
    pre_close = px(item.get("f60"))
    if price and pre_close and abs(price - pre_close) / pre_close > 0.25:
        price = float(item.get("f43", 0)) / 100.0 if item.get("f43") else price

    return {
        "code": STOCK_CODE,
        "name": item.get("f58", ""),
        "price": price,
        "open": px(item.get("f46")),
        "high": px(item.get("f44")),
        "low": px(item.get("f45")),
        "pre_close": pre_close,
        "volume": item.get("f47"),
        "amount": item.get("f48"),
        "turnover_pct": float(item.get("f168", 0) or 0) / 100.0,
        "change_pct": float(item.get("f170", 0) or 0) / 100.0,
        "source": "eastmoney",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def _eastmoney_klines(days=HISTORY_DAYS, secid=None):
    secid = secid or SECID
    url = (
        "https://push2his.eastmoney.com/api/qt/stock/kline/get?"
        + urllib.parse.urlencode(
            {
                "secid": secid,
                "fields1": "f1,f2,f3,f4,f5,f6",
                "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
                "klt": "101",
                "fqt": "1",
                "end": "20500101",
                "lmt": str(days),
                "ut": "fa5fd1943c7b386f172d6893dbfbaeb4",
            }
        )
    )
    data = _get(url)
    klines = (data.get("data") or {}).get("klines") or []
    rows = []
    for line in klines:
        parts = line.split(",")
        if len(parts) < 11:
            continue
        rows.append(
            {
                "date": parts[0],
                "open": float(parts[1]),
                "close": float(parts[2]),
                "high": float(parts[3]),
                "low": float(parts[4]),
                "volume": int(float(parts[5])),
                "amount": float(parts[6]),
                "amplitude_pct": float(parts[7]),
                "change_pct": float(parts[8]),
                "change": float(parts[9]),
                "turnover_pct": float(parts[10]),
                "source": "eastmoney",
            }
        )
    return rows


def resolve_source(source=None):
    src = (source or DATA_SOURCE or "ths").lower()
    if src == "auto":
        try:
            from ifind_fetcher import is_available
            if is_available():
                return "ifind"
        except ImportError:
            pass
        return "ths"
    return src


def fetch_daily_klines(days=HISTORY_DAYS, source=None):
    src = resolve_source(source)
    if src == "ths":
        from ths_fetcher import fetch_daily_klines as fn
        return fn(days)
    if src == "ifind":
        from ifind_fetcher import fetch_daily_klines as fn
        return fn(days)
    if src == "eastmoney":
        return _eastmoney_klines(days)
    raise ValueError("未知数据源: {} (可选 ths/eastmoney/ifind/auto)".format(src))


def fetch_realtime(source=None):
    src = resolve_source(source)
    if src == "ths":
        from ths_fetcher import fetch_realtime as fn
        return fn()
    if src == "ifind":
        from ifind_fetcher import fetch_realtime as fn
        return fn()
    if src == "eastmoney":
        return _eastmoney_realtime()
    raise ValueError("未知数据源: {}".format(src))


def get_source_label(source=None):
    labels = {"ths": "同花顺", "eastmoney": "东方财富", "ifind": "同花顺 iFinD"}
    return labels.get(resolve_source(source), resolve_source(source))


def save_cache(klines, source=None):
    os.makedirs(DATA_CACHE_DIR, exist_ok=True)
    src = resolve_source(source)
    path = os.path.join(DATA_CACHE_DIR, "688249_daily_{}.json".format(src))
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"updated": datetime.now().isoformat(), "source": src, "klines": klines}, f, ensure_ascii=False, indent=2)
    return path


def load_cache(source=None):
    src = resolve_source(source)
    path = os.path.join(DATA_CACHE_DIR, "688249_daily_{}.json".format(src))
    if not os.path.isfile(path):
        path = os.path.join(DATA_CACHE_DIR, "688249_daily.json")
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_benchmark_klines(days=HISTORY_DAYS):
    """拉取做T基准股（华虹公司）日K"""
    from config import BENCHMARK
    return _eastmoney_klines(days=days, secid=BENCHMARK["secid"])


def open_ths_page():
    import webbrowser
    from ths_fetcher import stock_page_url
    url = stock_page_url()
    webbrowser.open(url)
    return url
