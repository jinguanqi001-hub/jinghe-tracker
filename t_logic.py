# -*- coding: utf-8 -*-
"""T仓华虹基准信号 — v9.3 大波段做T (0↔25%)"""

from config import T_THRESHOLDS


def is_bull_mode(sig, mb=0):
    """保留供 tracker 展示，v9.3 不再强制锁满"""
    if not sig:
        return False
    return bool(sig.get("uptrend") or sig.get("px", 0) > sig.get("ma10", 0) or mb >= 1)


def score_hh_t_signals(hh_px, hh_op, hh_hi, hh_lo, hh_ma5, hh_ma10, hh_rsi, hh_intraday,
                       hh_upper, hh_vr, hh_chg, jh_chg):
    """华虹基准做T评分。"""
    th = T_THRESHOLDS
    score = 0
    notes = []

    if hh_lo <= hh_ma5 * 1.012 and hh_px > hh_op and hh_intraday > 0.004:
        score += 2
        notes.append("华虹探底回升")
    if hh_lo <= hh_ma10 * 1.012 and hh_px > hh_ma10 and hh_px > hh_op:
        score += 1
        notes.append("华虹MA10企稳")
    if hh_rsi <= 38 and hh_px > hh_op:
        score += 2
        notes.append("华虹RSI超卖反弹")

    if hh_upper >= th["upper_shadow"] and hh_vr >= th["vr_sell_strong"]:
        score -= 2
        notes.append("华虹天量上影")
    if hh_vr >= th["vr_sell_strong"] and hh_px < hh_op and hh_chg < -0.01:
        score -= 1
        notes.append("华虹放量长阴")
    if hh_rsi >= th["rsi_sell"]:
        score -= 1
        notes.append("华虹RSI超买")

    if hh_chg < -0.01 and jh_chg > hh_chg + 0.005:
        score += 1
        notes.append("华虹弱晶合强")
    if hh_chg > 0.03 and jh_chg < hh_chg - 0.015:
        score -= 1
        notes.append("华虹强晶合弱")

    return score, notes


def t_pct_from_score(score, t_max, t_mid, prev_t=None, bull_lock=False):
    """
    v9.3: T仓大波段 0↔25%
    - score >= buy_full → 加满T
    - score <= sell_clear → T全出(0%)
    - 其余 → 维持上一档
    """
    th = T_THRESHOLDS
    if score >= th["buy_score_full"]:
        return t_max, "T加满"
    if score <= th["sell_score_clear"]:
        return 0.0, "T全出"
    if prev_t is not None:
        return prev_t, "T持有"
    return t_max, "T初始满"


def core_should_exit(ms, sig):
    """底仓清仓：仅三重确认"""
    if ms > -8:
        return False
    px = sig.get("px", 0)
    return px < sig.get("ma20", px) and px < sig.get("op", px)


def core_should_enter(mb, sig):
    if mb >= 1:
        return True
    if sig.get("uptrend"):
        return True
    return sig.get("px", 0) > sig.get("ma20", 0)
