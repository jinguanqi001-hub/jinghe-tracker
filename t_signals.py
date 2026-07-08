# -*- coding: utf-8 -*-
"""25% T仓信号 — 以华虹公司(688347)为基准"""

from config import BENCHMARK, POSITION
from data_fetcher import fetch_benchmark_klines
from indicators import compute_all, rsi


def _sig(level, message, action):
    return {"level": level, "message": message, "action": action}


def evaluate_t_trading(jh_klines, jh_realtime=None):
    """
    计算 T 仓建议 (0 / 12.5% / 25%)，基准为华虹公司。
    jh_klines: 晶合日K
    """
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

    signals = []
    score = 0

    if hh_lo <= hh_ma5 * 1.012 and hh_px > hh_op and hh_intraday > 0.004:
        score += 2
        signals.append(_sig("BUY", "华虹探底回升", "T仓加满至25%"))
    if hh_lo <= hh_ma10 * 1.012 and hh_px > hh_ma10 and hh_px > hh_op:
        score += 1
        signals.append(_sig("BUY", "华虹MA10企稳", "T仓加至12.5%"))
    if hh_rsi <= 38 and hh_px > hh_op:
        score += 2
        signals.append(_sig("BUY", "华虹RSI超卖反弹 (RSI {:.1f})".format(hh_rsi), "T仓加满"))
    if hh_upper >= 0.40 and hh_vr >= 1.55:
        score -= 3
        signals.append(_sig("SELL", "华虹放量上影", "T仓清空"))
    if hh_vr >= 1.90 and hh_px < hh_op:
        score -= 2
        signals.append(_sig("SELL", "华虹放量阴线", "T仓减至6%"))
    if hh_rsi >= 78:
        score -= 2
        signals.append(_sig("SELL", "华虹RSI超买 (RSI {:.1f})".format(hh_rsi), "T仓清空"))
    if hh_chg < -0.01 and jh_chg > hh_chg + 0.005:
        score += 1
        signals.append(_sig("BUY", "华虹弱于晶合 — 补涨窗口", "T仓加"))
    if hh_chg > 0.02 and jh_chg < hh_chg - 0.01:
        score -= 1
        signals.append(_sig("SELL", "华虹强于晶合 — 晶合滞后", "T仓减"))

    if score >= 3:
        t_pct, t_action = POSITION["t_max_pct"], "T加满(25%)"
    elif score >= 1:
        t_pct, t_action = POSITION["t_mid_pct"], "T半仓(12.5%)"
    elif score <= -3:
        t_pct, t_action = 0.0, "T清空(0%)"
    elif score <= -1:
        t_pct, t_action = POSITION["t_mid_pct"] * 0.5, "T减至(6%)"
    else:
        t_pct, t_action = POSITION["t_mid_pct"], "T持有(12.5%)"

    core_pct = POSITION["core_pct"]
    return {
        "benchmark": BENCHMARK["name"],
        "benchmark_code": BENCHMARK["code"],
        "benchmark_price": hh_px,
        "benchmark_change_pct": hh.get("change_pct"),
        "benchmark_rsi": hh_rsi,
        "t_pct": t_pct,
        "t_action": t_action,
        "core_pct": core_pct,
        "total_pct": min(core_pct + t_pct, 1.0),
        "score": score,
        "signals": signals,
    }
