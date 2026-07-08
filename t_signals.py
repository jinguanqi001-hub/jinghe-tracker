# -*- coding: utf-8 -*-
"""25% T仓信号 — 以华虹公司(688347)为基准"""

from config import BENCHMARK, POSITION
from data_fetcher import fetch_benchmark_klines
from indicators import rsi
from t_logic import score_hh_t_signals, t_pct_from_score


def _sig(level, message, action):
    return {"level": level, "message": message, "action": action}


def evaluate_t_trading(jh_klines, jh_realtime=None):
    """计算 T 仓建议 (0 / 12.5% / 25%)，基准为华虹公司。"""
    try:
        hh_klines = fetch_benchmark_klines()
    except Exception as e:
        return {
            "error": str(e),
            "t_pct": POSITION["t_mid_pct"],
            "t_action": "T持有(无华虹数据)",
            "signals": [],
            "benchmark": BENCHMARK["name"],
        }

    if len(hh_klines) < 22 or len(jh_klines) < 2:
        return {
            "t_pct": POSITION["t_mid_pct"],
            "t_action": "T持有",
            "signals": [],
            "benchmark": BENCHMARK["name"],
        }

    hh = hh_klines[-1]
    hh_prev = hh_klines[-2]
    jh = jh_klines[-1]
    jh_prev = jh_klines[-2]

    hh_closes = [b["close"] for b in hh_klines]
    hh_op, hh_hi, hh_lo, hh_px = hh["open"], hh["high"], hh["low"], hh["close"]
    hh_ma5 = sum(hh_closes[-5:]) / 5
    hh_ma10 = sum(hh_closes[-10:]) / 10
    hh_rsi = rsi(hh_closes) or 50.0
    hh_intraday = (hh_px - hh_op) / hh_op if hh_op else 0.0
    hh_body = abs(hh_px - hh_op) if abs(hh_px - hh_op) > 0.01 else 0.01
    hh_upper = (hh_hi - max(hh_op, hh_px)) / hh_body

    hh_vols = [b["volume"] for b in hh_klines]
    hh_vma5 = sum(hh_vols[-6:-1]) / 5 if len(hh_vols) >= 6 else float(hh_vols[-1] or 1)
    hh_vr = float(hh_vols[-1] or 0) / hh_vma5 if hh_vma5 > 0 else 1.0

    hh_chg = (hh_px - hh_prev["close"]) / hh_prev["close"] if hh_prev["close"] else 0.0
    jh_chg = (jh["close"] - jh_prev["close"]) / jh_prev["close"] if jh_prev["close"] else 0.0

    score, notes = score_hh_t_signals(
        hh_px, hh_op, hh_hi, hh_lo, hh_ma5, hh_ma10, hh_rsi, hh_intraday,
        hh_upper, hh_vr, hh_chg, jh_chg,
    )

    signals = []
    for n in notes:
        if any(k in n for k in ("回升", "企稳", "超卖", "弱晶合")):
            signals.append(_sig("BUY", n, "T仓加"))
        else:
            signals.append(_sig("SELL", n, "T仓减"))

    t_pct, t_action = t_pct_from_score(score, POSITION["t_max_pct"], POSITION["t_mid_pct"])
    t_action = {"T加满": "T加满(25%)", "T半仓": "T半仓(12.5%)", "T清空": "T清空(0%)",
                "T减至¼": "T减至(6%)", "T持有": "T持有(12.5%)"}.get(t_action, t_action)

    return {
        "benchmark": BENCHMARK["name"],
        "benchmark_code": BENCHMARK["code"],
        "benchmark_price": hh_px,
        "benchmark_change_pct": hh.get("change_pct"),
        "benchmark_rsi": hh_rsi,
        "t_pct": t_pct,
        "t_action": t_action,
        "core_pct": POSITION["core_pct"],
        "total_pct": min(POSITION["core_pct"] + t_pct, 1.0),
        "score": score,
        "signals": signals,
    }
