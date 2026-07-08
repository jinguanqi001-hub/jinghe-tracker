# -*- coding: utf-8 -*-
"""隔日T逻辑 — 华虹(688347)基准，75%底仓 + 0~25% T仓，可隔夜"""

from config import OVERNIGHT_T, POSITION
from t_logic import score_hh_t_signals


def score_overnight_hh(hh_sig, hh_hist, jh_hist, jh_sig=None, jh_rsi_fn=None):
    """华虹隔日T评分（基础 + 可选扩展）"""
    th = OVERNIGHT_T
    hh = hh_hist[-1]
    hh_chg = jh_chg = 0.0
    if len(hh_hist) >= 2:
        hh_chg = (hh_hist[-1]["close"] - hh_hist[-2]["close"]) / hh_hist[-2]["close"]
    if len(jh_hist) >= 2:
        jh_chg = (jh_hist[-1]["close"] - jh_hist[-2]["close"]) / jh_hist[-2]["close"]

    score, notes = score_hh_t_signals(
        hh_sig["px"], hh_sig["op"], hh["high"], hh_sig["lo"],
        hh_sig["ma5"], hh_sig["ma10"], hh_sig["rsi"], hh_sig["intraday"],
        hh_sig["upper"], hh_sig["vr"], hh_chg, jh_chg,
    )

    if th.get("jh_rsi_sell") and jh_hist and jh_rsi_fn:
        jh_rsi = jh_rsi_fn([b["close"] for b in jh_hist])
        ma20 = sum(b["close"] for b in jh_hist[-20:]) / min(20, len(jh_hist))
        dev = (jh_sig["px"] - ma20) / ma20 if ma20 and jh_sig else 0
        if (jh_rsi and jh_rsi >= th["jh_rsi_sell"]
                and dev >= th.get("jh_rsi_dev", 0.15)
                and hh_sig["upper"] >= th.get("jh_rsi_shadow", 0.35)):
            score -= th.get("jh_rsi_penalty", 2)
            notes.append("晶合超涨+华虹上影")

    if th.get("hh_gap_sell") and hh_chg > th["hh_gap_sell"] and jh_chg < hh_chg - th.get("hh_gap_jh_lag", 0.02):
        score -= th.get("hh_gap_penalty", 2)
        notes.append("华虹涨晶合跟不上")

    if th.get("confirm_sell") and score <= th["sell_score_clear"] and jh_sig:
        if jh_sig.get("px", 0) >= jh_sig.get("op", 0) and jh_chg > 0:
            score += th.get("confirm_dampen", 1)
            notes.append("晶合仍强(卖信号减弱)")

    return score, notes


def t_pct_overnight(score, prev_t=None, uptrend=False):
    """隔日T仓位：score≥2加满 / score≤-2全出 / 其余持有"""
    th = OVERNIGHT_T
    t_max = POSITION["t_max_pct"]
    t_mid = POSITION["t_mid_pct"]
    t_min = t_mid if (uptrend and th.get("trend_floor")) else 0.0

    if score >= th["buy_score_full"]:
        return t_max, "T加满"
    if score <= th["sell_score_clear"]:
        if uptrend and th.get("trend_floor") and score > th.get("sell_score_force", -5):
            return t_mid, "趋势T保护"
        return t_min, "T全出"
    if prev_t is not None:
        return prev_t, "T持有"
    return t_max, "T初始满"
