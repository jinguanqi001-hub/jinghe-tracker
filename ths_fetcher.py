# -*- coding: utf-8 -*-
"""同花顺公开行情 API（d.10jqka.com.cn，无需 iFinD 账号）"""

import json
import re
import ssl
import urllib.request
from datetime import datetime

from ths_config import THS_CODE, THS_PUBLIC

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


def fetch_realtime():
    """从同花顺分时接口获取最新价"""
    url = THS_PUBLIC["intraday_url"].format(code=THS_CODE)
    payload = _parse_jsonp(_fetch_text(url))
    block = payload.get(THS_CODE) or (payload[list(payload.keys())[0]] if payload else {})
    if not block:
        raise RuntimeError("同花顺分时数据为空")

    pre_close = float(block.get("pre") or 0)
    name = block.get("name", "")
    ticks = [t for t in (block.get("data") or "").split(";") if t.strip()]

    price = open_px = high = low = None
    volume = amount = 0
    if ticks:
        last = ticks[-1].split(",")
        if len(last) >= 5:
            price = float(last[1])
            amount = float(last[2])
            volume = int(float(last[4]))
        first = ticks[0].split(",")
        open_px = float(first[1]) if len(first) >= 2 else price
        prices = [float(t.split(",")[1]) for t in ticks if len(t.split(",")) >= 2]
        if prices:
            high = max(prices)
            low = min(prices)

    if price is None:
        raise RuntimeError("无法解析同花顺实时价")

    change_pct = ((price - pre_close) / pre_close * 100) if pre_close else 0.0
    date_raw = block.get("date", "")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if len(date_raw) == 8:
        ts = "{}-{}-{} {}".format(
            date_raw[:4], date_raw[4:6], date_raw[6:8], datetime.now().strftime("%H:%M:%S")
        )

    klines = fetch_daily_klines(days=1)
    turnover = klines[-1]["turnover_pct"] if klines else None

    return {
        "code": "688249",
        "name": name,
        "price": price,
        "open": open_px or price,
        "high": high or price,
        "low": low or price,
        "pre_close": pre_close,
        "volume": volume,
        "amount": amount,
        "turnover_pct": turnover,
        "change_pct": round(change_pct, 2),
        "source": "ths",
        "timestamp": ts,
    }


def stock_page_url():
    return THS_PUBLIC["stock_page"].format(code="688249")
