# -*- coding: utf-8 -*-
"""25% 隔日T仓信号 — v11 华虹基准，可隔夜"""

from config import BENCHMARK, OVERNIGHT_T, POSITION
from data_fetcher import fetch_benchmark_klines
from indicators import rsi
from overnight_t_logic import score_overnight_hh, t_pct_overnight


def _sig(level, message, action):
    return {"level": level, "message": message, "action": action}


def _hh_vol_proxy(hh_klines):
    """构造 score_overnight_hh 所需的 hh_sig 字段"""
    if len(hh_klines) < 10:
        return None
    hh = hh_klines[-1]
    hh_closes = [b["close"] for b in hh_klines]
    hh_vols = [b["volume"] for b in hh_klines]
    hh_op, hh_hi, hh_lo, hh_px = hh["open"], hh["high"], hh["low"], hh["close"]
    hh_ma5 = sum(hh_closes[-5:]) / 5
    hh_ma10 = sum(hh_closes[-10:]) / 10
    hh_rsi = rsi(hh_closes) or 50.0
    hh_intraday = (hh_px - hh_op) / hh_op if hh_op else 0.0
    hh_body = abs(hh_px - hh_op) if abs(hh_px - hh_op) > 0.01 else 0.01
    hh_upper = (hh_hi - max(hh_op, hh_px)) / hh_body
    hh_vma5 = sum(hh_vols[-6:-1]) / 5 if len(hh_vols) >= 6 else float(hh_vols[-1] or 1)
    hh_vr = float(hh_vols[-1] or 0) / hh_vma5 if hh_vma5 > 0 else 1.0
    return {
        "px": hh_px, "op": hh_op, "lo": hh_lo, "ma5": hh_ma5, "ma10": hh_ma10,
        "rsi": hh_rsi, "intraday": hh_intraday, "upper": hh_upper, "vr": hh_vr,
    }


def evaluate_t_trading(jh_klines, jh_realtime=None):
    """v11 隔日T: 华虹信号 + min_days 冷却提示"""
    try:
        hh_klines = fetch_benchmark_klines()
    except Exception as e:
        return {
            "error": str(e),
            "mode": "overnight",
            "t_pct": POSITION["t_max_pct"],
            "t_action": "T持有(无华虹数据)",
            "signals": [],
            "benchmark": BENCHMARK["name"],
        }

    if len(hh_klines) < 22 or len(jh_klines) < 22:
        return {
            "mode": "overnight",
            "t_pct": POSITION["t_max_pct"],
            "t_action": "T初始满",
            "signals": [],
            "benchmark": BENCHMARK["name"],
        }

    hh_sig = _hh_vol_proxy(hh_klines)
    if not hh_sig:
        return {"mode": "overnight", "t_pct": POSITION["t_max_pct"], "t_action": "T初始满", "signals": []}

    jh_closes = [b["close"] for b in jh_klines]
    ma5 = sum(jh_closes[-5:]) / 5
    ma10 = sum(jh_closes[-10:]) / 10
    ma20 = sum(jh_closes[-20:]) / 20
    jh_px = jh_closes[-1]
    jh_sig = {
        "px": jh_px,
        "op": jh_klines[-1]["open"],
        "uptrend": jh_px > ma20 and ma5 > ma10 > ma20,
    }

    score, notes = score_overnight_hh(hh_sig, hh_klines, jh_klines, jh_sig=jh_sig, jh_rsi_fn=rsi)
    prev_t = POSITION["t_max_pct"]
    t_pct, t_action = t_pct_overnight(score, prev_t=prev_t, uptrend=jh_sig["uptrend"])
    labels = {
        "T加满": "T加满(25%) → 总仓100%",
        "T全出": "T全出(0%) → 总仓75%",
        "T持有": "T持有(隔日)",
        "T初始满": "T初始满(25%)",
        "趋势T保护": "趋势T保护(12.5%)",
    }
    t_action = labels.get(t_action, t_action)
    if OVERNIGHT_T.get("min_days"):
        t_action += " [冷却{}日]".format(OVERNIGHT_T["min_days"])

    signals = []
    for n in notes:
        lvl = "BUY" if any(k in n for k in ("回升", "企稳", "超卖", "弱晶合")) else "SELL"
        signals.append(_sig(lvl, n, t_action))

    hh = hh_klines[-1]
    core_pct = POSITION["core_pct"]
    return {
        "mode": "overnight",
        "benchmark": BENCHMARK["name"],
        "benchmark_code": BENCHMARK["code"],
        "benchmark_price": hh["close"],
        "benchmark_change_pct": hh.get("change_pct"),
        "benchmark_rsi": hh_sig["rsi"],
        "t_pct": t_pct,
        "t_action": t_action,
        "core_pct": core_pct,
        "total_pct": min(core_pct + t_pct, 1.0),
        "score": score,
        "min_days": OVERNIGHT_T.get("min_days", 0),
        "signals": signals,
    }
