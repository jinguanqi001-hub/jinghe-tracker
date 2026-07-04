# -*- coding: utf-8 -*-
"""同花顺 vs 东方财富 双源对比"""

from config import STOCK_CODE

# 价差超过此比例(%) 触发 WARN
PRICE_DIFF_WARN_PCT = 0.3
TURNOVER_DIFF_WARN = 0.5


def _safe_pct_diff(a, b):
    if a is None or b is None or b == 0:
        return None
    return (a - b) / abs(b) * 100


def compare_realtime(ths_rt, em_rt):
    ths_p = ths_rt.get("price")
    em_p = em_rt.get("price")
    price_diff = None
    if ths_p is not None and em_p is not None:
        price_diff = ths_p - em_p

    ths_chg = ths_rt.get("change_pct")
    em_chg = em_rt.get("change_pct")
    ths_to = ths_rt.get("turnover_pct")
    em_to = em_rt.get("turnover_pct")

    alerts = []
    price_diff_pct = _safe_pct_diff(ths_p, em_p)
    if price_diff_pct is not None and abs(price_diff_pct) >= PRICE_DIFF_WARN_PCT:
        alerts.append(
            {
                "level": "WARN",
                "message": "双源价差 {:.2f}% (同花顺 {} vs 东财 {})".format(
                    price_diff_pct, ths_p, em_p
                ),
            }
        )

    if ths_to is not None and em_to is not None and abs(ths_to - em_to) >= TURNOVER_DIFF_WARN:
        alerts.append(
            {
                "level": "INFO",
                "message": "换手率差异 {:.2f}pct (同花顺 {}% vs 东财 {}%)".format(
                    ths_to - em_to, ths_to, em_to
                ),
            }
        )

    consistent = not any(a["level"] == "WARN" for a in alerts)
    return {
        "stock_code": STOCK_CODE,
        "ths": ths_rt,
        "eastmoney": em_rt,
        "price_diff": price_diff,
        "price_diff_pct": price_diff_pct,
        "change_diff": (ths_chg - em_chg) if ths_chg is not None and em_chg is not None else None,
        "turnover_diff": (ths_to - em_to) if ths_to is not None and em_to is not None else None,
        "alerts": alerts,
        "consistent": consistent,
    }


def compare_klines(ths_klines, em_klines, days=5):
    """对比最近 N 日 K 线收盘价"""
    ths_map = {b["date"]: b for b in ths_klines[-days:]}
    em_map = {b["date"]: b for b in em_klines[-days:]}
    dates = sorted(set(ths_map.keys()) & set(em_map.keys()))
    rows = []
    max_diff = 0.0
    for d in dates:
        tc = ths_map[d]["close"]
        ec = em_map[d]["close"]
        diff_pct = _safe_pct_diff(tc, ec) or 0.0
        max_diff = max(max_diff, abs(diff_pct))
        rows.append({"date": d, "ths_close": tc, "em_close": ec, "diff_pct": diff_pct})
    return {"rows": rows, "max_close_diff_pct": max_diff, "days": len(rows)}


def run_full_compare():
    from data_fetcher import fetch_daily_klines, fetch_realtime

    ths_rt = fetch_realtime(source="ths")
    em_rt = fetch_realtime(source="eastmoney")
    rt_cmp = compare_realtime(ths_rt, em_rt)

    ths_k = fetch_daily_klines(source="ths")
    em_k = fetch_daily_klines(source="eastmoney")
    k_cmp = compare_klines(ths_k, em_k, days=5)

    return {"realtime": rt_cmp, "klines": k_cmp}
