# -*- coding: utf-8 -*-
"""T仓华虹基准信号 + v9.2 趋势锁满逻辑"""

from config import T_THRESHOLDS


def is_bull_mode(sig, mb=0):
    """趋势/多头模式：锁满 75%+25%=100%"""
    if not sig:
        return False
    return bool(sig.get("uptrend") or sig.get("px", 0) > sig.get("ma10", 0) or mb >= 1)


def score_hh_t_signals(hh_px, hh_op, hh_hi, hh_lo, hh_ma5, hh_ma10, hh_rsi, hh_intraday,
                       hh_upper, hh_vr, hh_chg, jh_chg):
    """华虹基准做T评分。正=加仓，负=减仓。仅在非趋势锁时生效。"""
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
    """根据评分映射 T 仓比例。趋势锁定时直接满T。"""
    if bull_lock:
        return t_max, "趋势锁满"
    th = T_THRESHOLDS
    t_min = th.get("t_min_pct", t_mid)
    if score >= th["buy_score_full"]:
        return t_max, "T加满"
    if score >= th["buy_score_mid"]:
        return max(t_mid, t_min), "T半仓"
    if score <= th["sell_score_clear"]:
        return t_min, "T下限"  # v9.2: 不清零，维持半T
    if score <= th["sell_score_cut"]:
        return max(t_mid, t_min), "T持有"
    if prev_t is not None and prev_t >= t_min:
        return prev_t, "T持有"
    return max(t_mid, t_min), "T持有"


def core_should_exit(ms, sig):
    """底仓清仓：仅三重确认"""
    if ms > -8:
        return False
    px = sig.get("px", 0)
    return px < sig.get("ma20", px) and px < sig.get("op", px)


def core_should_enter(mb, sig):
    """底仓建仓"""
    if mb >= 1:
        return True
    if sig.get("uptrend"):
        return True
    return sig.get("px", 0) > sig.get("ma20", 0)
