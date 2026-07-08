# -*- coding: utf-8 -*-
"""同花顺公开行情 API（d.10jqka.com.cn，无需 iFinD 账号）"""

import json
import re
import ssl
import urllib.request
from datetime import datetime

from ths_config import THS_BENCHMARK_CODE, THS_CODE, THS_PUBLIC

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": UA,
    "Referer": "https://stockpage.10jqka.com.cn/",
}


def _fetch_text(url, timeout=15):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _parse_jsonp(text):
    m = re.search(r"\((\{.*\})\)\s*;?\s*$", text, re.DOTALL)
    if not m:
        raise RuntimeError("同花顺返回格式异常")
    return json.loads(m.group(1))


def fetch_daily_klines(days=120):
    """从同花顺拉取日 K（前复权 01）"""
    url = THS_PUBLIC["kline_url"].format(code=THS_CODE)
    payload = _parse_jsonp(_fetch_text(url))
    raw = payload.get("data") or ""
    rows = []
    for seg in raw.split(";"):
        if not seg.strip():
            continue
        p = seg.split(",")
        if len(p) < 8:
            continue
        o, h, l, c = float(p[1]), float(p[2]), float(p[3]), float(p[4])
        vol_raw = int(float(p[5]))
        amount = float(p[6])
        turnover = float(p[7]) if p[7] else 0.0
        prev_close = rows[-1]["close"] if rows else c
        change = c - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0.0
        amp = ((h - l) / prev_close * 100) if prev_close else 0.0
        rows.append(
            {
                "date": "{}-{}-{}".format(p[0][:4], p[0][4:6], p[0][6:8]),
                "open": o,
                "close": c,
                "high": h,
                "low": l,
                "volume": vol_raw // 100,
                "amount": amount,
                "amplitude_pct": round(amp, 2),
                "change_pct": round(change_pct, 2),
                "change": round(change, 2),
                "turnover_pct": turnover,
                "source": "ths",
            }
        )
    if days and len(rows) > days:
        rows = rows[-days:]
    return rows


def _parse_ticks(raw_data):
    """解析同花顺分时 tick 串 → [{time, price, amount, vwap, volume}, ...]"""
    ticks = []
    for seg in (raw_data or "").split(";"):
        if not seg.strip():
            continue
        p = seg.split(",")
        if len(p) < 5:
            continue
        ticks.append(
            {
                "time": p[0],
                "price": float(p[1]),
                "amount": float(p[2]),
                "vwap": float(p[3]),
                "volume": int(float(p[4])),
            }
        )
    return ticks


def fetch_intraday(code=None):
    """拉取同花顺分时 tick（晶合/华虹通用）"""
    code = code or THS_CODE
    url = THS_PUBLIC["intraday_url"].format(code=code)
    payload = _parse_jsonp(_fetch_text(url))
    block = payload.get(code) or (payload[list(payload.keys())[0]] if payload else {})
    if not block:
        raise RuntimeError("同花顺分时数据为空: {}".format(code))

    pre_close = float(block.get("pre") or 0)
    ticks = _parse_ticks(block.get("data"))
    if not ticks:
        raise RuntimeError("同花顺分时 tick 为空: {}".format(code))

    prices = [t["price"] for t in ticks]
    px = prices[-1]
    open_px = prices[0]
    hi = max(prices)
    lo = min(prices)
    vwap = ticks[-1]["vwap"]
    prev_px = prices[-2] if len(prices) >= 2 else px

    date_raw = block.get("date", "")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if len(date_raw) == 8:
        ts = "{}-{}-{} {}".format(
            date_raw[:4], date_raw[4:6], date_raw[6:8], ticks[-1]["time"][:2] + ":" + ticks[-1]["time"][2:4]
        )

    return {
        "code": code.replace("hs_", ""),
        "name": block.get("name", ""),
        "price": px,
        "open": open_px,
        "high": hi,
        "low": lo,
        "pre_close": pre_close,
        "vwap": vwap,
        "prev_price": prev_px,
        "volume": ticks[-1]["volume"],
        "amount": ticks[-1]["amount"],
        "change_pct": round((px - pre_close) / pre_close * 100, 2) if pre_close else 0.0,
        "intraday_pct": round((px - open_px) / open_px, 4) if open_px else 0.0,
        "pullback_from_high": round((hi - px) / hi, 4) if hi else 0.0,
        "bounce_from_low": round((px - lo) / lo, 4) if lo else 0.0,
        "ticks": ticks,
        "tick_count": len(ticks),
        "last_time": ticks[-1]["time"],
        "source": "ths",
        "timestamp": ts,
    }


def fetch_realtime():
    """从同花顺分时接口获取晶合最新价"""
    intraday = fetch_intraday(THS_CODE)
    klines = fetch_daily_klines(days=1)
    turnover = klines[-1]["turnover_pct"] if klines else None
    return {
        "code": "688249",
        "name": intraday.get("name", ""),
        "price": intraday["price"],
        "open": intraday["open"],
        "high": intraday["high"],
        "low": intraday["low"],
        "pre_close": intraday["pre_close"],
        "volume": intraday["volume"],
        "amount": intraday["amount"],
        "turnover_pct": turnover,
        "change_pct": intraday["change_pct"],
        "source": "ths",
        "timestamp": intraday["timestamp"],
    }


def fetch_benchmark_intraday():
    """华虹公司分时 tick — T仓基准"""
    return fetch_intraday(THS_BENCHMARK_CODE)


def stock_page_url():
    return THS_PUBLIC["stock_page"].format(code="688249")
