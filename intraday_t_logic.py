# -*- coding: utf-8 -*-
"""日内T逻辑 — 分钟级华虹(688347)基准，75%底仓 + 0~25% T仓"""

from config import BENCHMARK, INTRADAY_T, POSITION
from indicators import rsi


def _minute_closes(ticks, step=5):
    """每 step 个 tick 取收盘价，用于分钟 RSI"""
    if not ticks:
        return []
    closes = []
    for i in range(step - 1, len(ticks), step):
        closes.append(ticks[i]["price"])
    if ticks and (not closes or closes[-1] != ticks[-1]["price"]):
        closes.append(ticks[-1]["price"])
    return closes


def score_intraday_hh(hh, jh, hh_daily=None):
    """
    华虹日内T评分（分钟/tick 级）。
    hh/jh: fetch_intraday 返回值
    """
    th = INTRADAY_T
    score = 0
    notes = []

    px = hh["price"]
    op = hh["open"]
    vwap = hh["vwap"]
    prev = hh.get("prev_price", px)
    pullback = hh.get("pullback_from_high", 0)
    bounce = hh.get("bounce_from_low", 0)
    intraday = hh.get("intraday_pct", 0)

    closes = _minute_closes(hh.get("ticks") or [], step=5)
    hh_rsi = rsi(closes, period=min(14, max(3, len(closes) - 1))) if len(closes) >= 5 else 50.0

    # --- 买入T (华虹探底回升) ---
    if pullback >= th["pullback_buy"] and px > prev and px >= vwap * 0.998:
        score += 2
        notes.append("华虹日内回落{}%后回升".format(round(pullback * 100, 1)))
    if bounce >= th["bounce_buy"] and px > op and px > prev:
        score += 1
        notes.append("华虹自低点反弹{}%".format(round(bounce * 100, 1)))
    if hh_rsi <= th["rsi_oversold"] and px > prev and px > vwap:
        score += 2
        notes.append("华虹分钟RSI超卖反弹({:.0f})".format(hh_rsi))
    if px <= hh["low"] * 1.005 and px > prev:
        score += 1
        notes.append("华虹接近日内低点转强")

    # --- 卖出T (华虹冲高转弱) ---
    if bounce >= th["spike_sell"] and px < prev and px < vwap:
        score -= 2
        notes.append("华虹日内拉升{}%后转弱".format(round(bounce * 100, 1)))
    if pullback >= th["drop_sell"] and px < prev and intraday < 0:
        score -= 1
        notes.append("华虹自高点回落{}%".format(round(pullback * 100, 1)))
    if hh_rsi >= th["rsi_overbought"] and px < prev:
        score -= 1
        notes.append("华虹分钟RSI超买({:.0f})".format(hh_rsi))
    if px > vwap * 1.012 and px < prev and intraday > 0.01:
        score -= 1
        notes.append("华虹偏离VWAP回落")

    # --- 相对强弱 (晶合 vs 华虹) ---
    jh_chg = jh.get("intraday_pct", 0)
    hh_chg = intraday
    gap = jh_chg - hh_chg
    if gap >= th["rel_strength_gap"]:
        score += 1
        notes.append("晶合强于华虹({:+.1f}%)".format(gap * 100))
    if gap <= -th["rel_strength_gap"] and hh_chg > 0.015:
        score -= 1
        notes.append("华虹强于晶合({:+.1f}%)".format(-gap * 100))

    return score, notes, hh_rsi


def t_pct_from_intraday_score(score, prev_t=None, last_time=None, uptrend=False):
    """日内T仓位 v10.1：分级调仓 + 趋势保护"""
    th = INTRADAY_T
    t_max = POSITION["t_max_pct"]
    t_mid = POSITION["t_mid_pct"]
    t_min = 0.0
    if uptrend and th.get("trend_lock"):
        t_min = t_mid

    if last_time and th.get("session_end_flatten") and last_time >= th.get("flatten_time", "14:50").replace(":", ""):
        return max(t_mid, t_min), "收盘T归位"

    if score >= th["buy_score_full"]:
        return t_max, "T加满"
    if score >= th.get("buy_score_mid", 2):
        target = max(t_mid, t_min)
        if prev_t is not None and prev_t >= t_max:
            return prev_t, "T持有"
        return target, "T半仓加"
    if score <= th["sell_score_clear"]:
        if uptrend and th.get("trend_lock") and score > th.get("sell_score_force", -4):
            return t_mid, "趋势T保护"
        return t_min, "T全出"
    if score <= th.get("sell_score_cut", -2):
        if uptrend and th.get("trend_lock"):
            return prev_t if prev_t is not None else t_max, "T持有"
        if prev_t is not None and prev_t <= t_min:
            return prev_t, "T持有"
        return max(t_mid, t_min), "T半仓减"
    if prev_t is not None:
        return prev_t, "T持有"
    return t_max, "T初始满"


def evaluate_intraday_t(hh_intraday, jh_intraday, prev_t=None, uptrend=False):
    """完整日内T评估"""
    score, notes, hh_rsi = score_intraday_hh(hh_intraday, jh_intraday)
    t_pct, t_action = t_pct_from_intraday_score(
        score, prev_t=prev_t, last_time=hh_intraday.get("last_time"), uptrend=uptrend,
    )
    core_pct = POSITION["core_pct"]
    labels = {
        "T加满": "T加满(25%) → 总仓100%",
        "T全出": "T全出(0%) → 总仓75%",
        "T持有": "T持有",
        "T半仓加": "T半仓加(12.5%) → 总仓87.5%",
        "T半仓减": "T半仓减(12.5%) → 总仓87.5%",
        "趋势T保护": "趋势T保护(12.5%) → 总仓87.5%",
        "T初始满": "T初始满(25%)",
        "收盘T归位": "收盘T归位(12.5%)",
    }
    return {
        "mode": "intraday",
        "benchmark": BENCHMARK["name"],
        "benchmark_code": BENCHMARK["code"],
        "benchmark_price": hh_intraday["price"],
        "benchmark_change_pct": hh_intraday.get("change_pct"),
        "benchmark_intraday_pct": round(hh_intraday.get("intraday_pct", 0) * 100, 2),
        "benchmark_rsi": round(hh_rsi, 1),
        "benchmark_vwap": hh_intraday.get("vwap"),
        "benchmark_time": hh_intraday.get("last_time"),
        "jh_price": jh_intraday["price"],
        "jh_intraday_pct": round(jh_intraday.get("intraday_pct", 0) * 100, 2),
        "score": score,
        "t_pct": t_pct,
        "t_action": labels.get(t_action, t_action),
        "core_pct": core_pct,
        "total_pct": min(core_pct + t_pct, 1.0),
        "signals": notes,
        "tick_count": hh_intraday.get("tick_count"),
    }
