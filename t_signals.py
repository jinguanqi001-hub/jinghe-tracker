# -*- coding: utf-8 -*-
"""25% T仓信号 — 以华虹公司(688347)为基准"""

from config import BENCHMARK, POSITION
from data_fetcher import fetch_benchmark_klines
from indicators import rsi
from t_logic import score_hh_t_signals, t_pct_from_score, is_bull_mode


def _sig(level, message, action):
    return {"level": level, "message": message, "action": action}


def evaluate_t_trading(jh_klines, jh_realtime=None):
    """计算 T 仓建议，v9.2 趋势锁满 + 震荡华虹做T。"""
    try:
        hh_klines = fetch_benchmark_klines()
    except Exception as e:
        return {
            "error": str(e),
            "t_pct": POSITION["t_max_pct"],
            "t_action": "T持有(无华虹数据)",
            "signals": [],
            "benchmark": BENCHMARK["name"],
        }

    if len(hh_klines) < 22 or len(jh_klines) < 2:
        return {
            "t_pct": POSITION["t_max_pct"],
            "t_action": "T持有",
            "signals": [],
            "benchmark": BENCHMARK["name"],
        }

    hh = hh_klines[-1]
    hh_prev = hh_klines[-2]
    jh = jh_klines[-1]
    jh_prev = jh_klines[-2]

    hh_closes = [b["close"] for b in hh_klines]
    jh_closes = [b["close"] for b in jh_klines]
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

    jh_ma5 = sum(jh_closes[-5:]) / 5
    jh_ma10 = sum(jh_closes[-10:]) / 10
    jh_ma20 = sum(jh_closes[-20:]) / 20 if len(jh_closes) >= 20 else jh_ma10
    jh_sig = {
        "px": jh["close"], "ma5": jh_ma5, "ma10": jh_ma10, "ma20": jh_ma20,
        "uptrend": jh["close"] > jh_ma20 and jh_ma5 > jh_ma10 > jh_ma20,
    }
    bull = is_bull_mode(jh_sig, mb=1)

    if bull:
        t_pct = POSITION["t_max_pct"]
        t_action = "趋势锁满(100%)"
        signals = [_sig("INFO", "多头趋势 — 75%底仓+25%T锁满", "总仓位100%")]
    else:
        score, notes = score_hh_t_signals(
            hh_px, hh_op, hh_hi, hh_lo, hh_ma5, hh_ma10, hh_rsi, hh_intraday,
            hh_upper, hh_vr, hh_chg, jh_chg,
        )
        t_pct, t_action = t_pct_from_score(score, POSITION["t_max_pct"], POSITION["t_mid_pct"])
        t_action = {
            "T加满": "T加满(25%)", "T半仓": "T半仓(12.5%)", "T下限": "T下限(12.5%)",
            "T持有": "T持有", "趋势锁满": "趋势锁满(25%)",
        }.get(t_action, t_action)
        signals = []
        for n in notes:
            lvl = "BUY" if any(k in n for k in ("回升", "企稳", "超卖", "弱晶合")) else "SELL"
            signals.append(_sig(lvl, n, "T仓调整"))

    core_pct = POSITION["core_pct"]
    total = min(core_pct + t_pct, 1.0) if not bull else 1.0
    return {
        "benchmark": BENCHMARK["name"],
        "benchmark_code": BENCHMARK["code"],
        "benchmark_price": hh_px,
        "benchmark_change_pct": hh.get("change_pct"),
        "benchmark_rsi": hh_rsi,
        "t_pct": t_pct,
        "t_action": t_action,
        "core_pct": core_pct,
        "total_pct": total,
        "bull_lock": bull,
        "signals": signals,
    }
