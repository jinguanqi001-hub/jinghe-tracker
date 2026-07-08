#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地回测：v8 / v9(75%底仓+25%华虹做T) / 买入持有"""

import argparse
import copy
import json
import os

from config import INTRADAY_T, OVERNIGHT_T, POSITION
from data_fetcher import _eastmoney_klines, fetch_benchmark_klines
from intraday_t_logic import score_intraday_hh, t_pct_from_intraday_score
from overnight_t_logic import score_overnight_hh, t_pct_overnight
from t_logic import core_should_exit, core_should_enter, score_hh_t_signals, t_pct_from_score


CORE_PCT = POSITION["core_pct"]
T_MAX = POSITION["t_max_pct"]
T_MID = POSITION["t_mid_pct"]


def load_klines(path="data/688249_daily_ths.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f)["klines"]


def fetch_sina(symbol, days=280):
    import ssl
    import urllib.request

    url = (
        "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
        "CN_MarketData.getKLineData?symbol={}&scale=240&ma=no&datalen={}".format(symbol, days)
    )
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
        raw = json.loads(resp.read().decode("utf-8"))
    rows = []
    for b in raw:
        prev = rows[-1]["close"] if rows else float(b["close"])
        c = float(b["close"])
        rows.append(
            {
                "date": b["day"],
                "open": float(b["open"]),
                "close": c,
                "high": float(b["high"]),
                "low": float(b["low"]),
                "volume": int(float(b["volume"])),
                "change_pct": (c - prev) / prev * 100 if prev else 0.0,
                "turnover_pct": 0.0,
                "source": "sina",
            }
        )
    return rows


def fetch_online(days=280):
    try:
        from config import SECID
        jh = _eastmoney_klines(days=days, secid=SECID)
        hh = fetch_benchmark_klines(days=days)
        return jh, hh, "eastmoney"
    except Exception:
        jh = fetch_sina("sh688249", days)
        hh = fetch_sina("sh688347", days)
        return jh, hh, "sina"


def align_klines(jh, hh):
    hh_map = {b["date"]: b for b in hh}
    dates = [b["date"] for b in jh if b["date"] in hh_map]
    return [b for b in jh if b["date"] in hh_map], [hh_map[d] for d in dates]


def rsi(closes, n=14):
    if len(closes) < n + 1:
        return 50.0
    gs, ls = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gs.append(max(d, 0))
        ls.append(max(-d, 0))
    ag = sum(gs[-n:]) / n
    al = sum(ls[-n:]) / n
    if al == 0:
        return 100.0
    return 100 - 100 / (1 + ag / al)


def vol_signals(history, use_levels, params):
    if len(history) < 22:
        return None
    o = [b["open"] for b in history]
    h = [b["high"] for b in history]
    l = [b["low"] for b in history]
    c = [b["close"] for b in history]
    v = [b["volume"] for b in history]

    px, hi, lo, op = c[-1], h[-1], l[-1], o[-1]
    prev, prev2 = c[-2], c[-3]
    ma5 = sum(c[-5:]) / 5
    ma10 = sum(c[-10:]) / 10
    ma20 = sum(c[-20:]) / 20
    rsi_v = rsi(c)
    uptrend = px > ma20 and ma5 > ma10 > ma20

    vma5 = sum(v[-6:-1]) / 5 if len(v) >= 6 else float(v[-1] or 1)
    if vma5 <= 0:
        vma5 = 1.0
    vr = float(v[-1] or 0) / vma5
    denom = sum(v[-7:-2]) / 5 if len(v) >= 7 else vma5
    vr_prev = float(v[-2] or 0) / denom if denom > 0 else 1.0

    body = abs(px - op) if abs(px - op) > 0.01 else 0.01
    upper = (hi - max(op, px)) / body
    chg = (px - prev) / prev if prev else 0.0
    intraday = (px - op) / op if op else 0.0

    R67, R61, S58, S52 = params["R67"], params["R61"], params["S58"], params["S52"]
    VOL_BREAK = params["VOL_BREAK"]
    VOL_STRONG = params["VOL_STRONG"]
    VOL_CLIMAX = params["VOL_CLIMAX"]
    VOL_PANIC = params["VOL_PANIC"]

    buy = sell = 0
    if use_levels:
        if px > S58 and prev <= S58 * 1.005 and vr >= VOL_BREAK:
            buy += 3
        if px > S52 and prev2 <= S52 * 1.01 and prev > S52 * 0.995 and vr >= VOL_BREAK:
            buy += 2
        if px >= R61 * 0.98 and vr >= VOL_STRONG and upper >= 0.35:
            sell -= 2 if not uptrend else 1
        if hi >= R67 * 0.985 and px < R67 * 0.992 and vr >= VOL_BREAK:
            sell -= 3 if not uptrend else 1
        if px < S58 * 0.993 and px < op and chg < 0 and vr >= VOL_PANIC and max(c[-20:]) >= S58 * 0.95:
            sell -= 3
        if px < S52 * 0.995 and px < op and chg < 0 and vr >= VOL_PANIC and max(c[-20:]) >= S52 * 0.95:
            sell -= 4

    if px > ma20 and ma5 > ma10 and vr >= VOL_BREAK and px > op and chg > 0:
        buy += 1
    if px > ma20 and vr_prev < 0.85 and vr >= VOL_STRONG and px > op:
        buy += 3
    if lo <= ma10 * 1.012 and px > ma10 and vr >= VOL_BREAK and px > op:
        buy += 2
    if px > ma5 > ma10 > ma20 and 1.05 <= vr <= 1.7:
        buy += 1
    if params.get("ma20_pullback") and uptrend and lo <= ma20 * 1.015 and px > ma20 and px > op:
        buy += params.get("ma20_pullback_score", 3)
    if params.get("recovery_buy"):
        ret5 = (px - c[-6]) / c[-6] if len(c) >= 6 and c[-6] else 0.0
        if prev < ma10 and px > ma10 and px > op and vr >= VOL_BREAK:
            buy += params.get("recovery_buy_score", 4)
        if ret5 >= params.get("momentum_ret5", 0.12) and px > ma5 and px > op:
            buy += params.get("momentum_buy_score", 3)

    if vr >= VOL_CLIMAX and upper >= params.get("SHADOW_RATIO", 0.5):
        sell -= 3 if not uptrend else 1
    if vr >= VOL_CLIMAX and px < op:
        sell -= 3 if not uptrend else 2
    if vr >= VOL_CLIMAX and abs(chg) < 0.008:
        sell -= 2 if not uptrend else 1
    if px < ma10 and prev >= ma10 and px < op and vr >= VOL_PANIC:
        sell -= 2
    if px < ma20 and prev < ma20 and px < op and vr >= VOL_PANIC:
        sell -= 4
    if rsi_v >= params.get("rsi_sell", 85) and vr >= VOL_STRONG and not uptrend:
        sell -= 1

    return {
        "buy": buy, "sell": sell, "px": px, "uptrend": uptrend,
        "ma5": ma5, "ma10": ma10, "ma20": ma20, "vr": vr, "rsi": rsi_v,
        "intraday": intraday, "upper": upper, "op": op, "lo": lo,
    }


def merge_target_v8(mb, ms, params, uptrend):
    if mb >= 3 and ms > -4:
        return (params.get("pos_max", 0.98) if uptrend else params.get("pos_strong", 0.95)), "强买"
    if params.get("trend_hold") and uptrend and ms > params.get("trend_sell_floor", -5):
        if mb >= 1:
            return params.get("pos_max", 0.98), "趋势强持"
        if ms <= -1:
            return max(params.get("trend_min_pos", 0.88), 0.88), "趋势减仓"
        return params.get("trend_min_pos", 0.92), "趋势持有"
    if ms <= -8:
        return 0.0, "清仓"
    if ms <= -6:
        return params.get("pos_heavy_cut", 0.40), "重度减仓"
    if ms <= -3:
        return params.get("pos_light_cut", 0.70), "轻度减仓"
    if mb >= 4:
        return params.get("pos_max", 0.98), "强买"
    if mb >= 2:
        return 0.85, "买入"
    if mb >= 1:
        return 0.80, "偏多"
    if mb + ms <= -2:
        return 0.55, "偏空"
    return None, "观望"


def hh_t_sleeve(hh_hist, jh_hist, t_sleeve, jh_sig=None, last_t_day=0, day_idx=0):
    """v11 隔日T"""
    hh_sig = vol_signals(hh_hist, False, BASE_PARAMS)
    if not hh_sig:
        return t_sleeve
    if jh_sig is None:
        jh_sig = vol_signals(jh_hist, True, BASE_PARAMS)
    if day_idx - last_t_day < OVERNIGHT_T.get("min_days", 0):
        return t_sleeve
    score, _ = score_overnight_hh(hh_sig, hh_hist, jh_hist, jh_sig=jh_sig, jh_rsi_fn=rsi)
    uptrend = jh_sig.get("uptrend", False) if jh_sig else False
    t_pct, _ = t_pct_overnight(score, prev_t=t_sleeve, uptrend=uptrend)
    return t_pct


def hh_t_sleeve_legacy(hh_hist, jh_hist, t_sleeve, bull_lock=False):
    sig = vol_signals(hh_hist, False, BASE_PARAMS)
    if not sig:
        return t_sleeve
    hh_chg = jh_chg = 0.0
    if len(hh_hist) >= 2:
        hh_chg = (hh_hist[-1]["close"] - hh_hist[-2]["close"]) / hh_hist[-2]["close"]
    if len(jh_hist) >= 2:
        jh_chg = (jh_hist[-1]["close"] - jh_hist[-2]["close"]) / jh_hist[-2]["close"]
    score, _ = score_hh_t_signals(
        sig["px"], sig["op"], hh_hist[-1]["high"], sig["lo"],
        sig["ma5"], sig["ma10"], sig["rsi"], sig["intraday"],
        sig["upper"], sig["vr"], hh_chg, jh_chg,
    )
    t_pct, _ = t_pct_from_score(score, T_MAX, T_MID, prev_t=t_sleeve)
    return t_pct


def core_target_v9(mb, ms, sig, core_on, lb=0, fast_entry=False):
    """v9.2 底仓：快入慢出"""
    if core_should_exit(ms, sig):
        return 0.0, False
    if not core_on:
        if fast_entry and sig.get("px", 0) > sig.get("ma20", 0) * 0.95:
            return CORE_PCT, True
        if core_should_enter(mb, sig) or lb >= 2:
            return CORE_PCT, True
        return 0.0, False
    return CORE_PCT, True


def max_drawdown(equity_curve):
    peak = equity_curve[0]
    mdd = 0.0
    for v in equity_curve:
        peak = max(peak, v)
        dd = (peak - v) / peak if peak else 0
        mdd = max(mdd, dd)
    return mdd * 100


def t_roundtrip_success(trades):
    """统计 T全出→T加满 的回补成功率(买回价<卖出价)"""
    exits = []
    rounds = []
    for t in trades:
        t_pct = t.get("t")
        if t_pct == 0.0:
            exits.append(t)
        elif t_pct == T_MAX and exits:
            e = exits.pop(0)
            ok = t["px"] < e["px"]
            rounds.append({
                "sell_date": e["date"],
                "sell_px": e["px"],
                "buy_date": t["date"],
                "buy_px": t["px"],
                "ok": ok,
                "spread_pct": (e["px"] - t["px"]) / e["px"] * 100 if e["px"] else 0.0,
            })
    if not rounds:
        return 0, 0.0, []
    wins = sum(1 for r in rounds if r["ok"])
    return len(rounds), wins / len(rounds) * 100, rounds


BASE_PARAMS = {
    "R67": 67.0, "R61": 61.0, "S58": 58.0, "S52": 52.0,
    "VOL_BREAK": 1.30, "VOL_STRONG": 1.55, "VOL_CLIMAX": 1.90,
    "VOL_PANIC": 1.45, "SHADOW_RATIO": 0.50,
    "REBAL_MIN": 0.015, "r67_fail_need": 3, "r67_px_min": 62.0, "rsi_sell": 85,
    "ma20_pullback": True, "ma20_pullback_score": 3,
    "recovery_buy": True, "recovery_buy_score": 4,
    "momentum_ret5": 0.12, "momentum_buy_score": 3,
    "trend_hold": True, "trend_min_pos": 0.92, "trend_sell_floor": -5,
    "pos_max": 0.98, "pos_strong": 0.95, "pos_light_cut": 0.70, "pos_heavy_cut": 0.40,
}


def backtest_v8(klines, params, start_idx=21):
    cash, shares = 1.0, 0.0
    r67_fail, last_target = 0, -1.0
    rebal_min = params.get("REBAL_MIN", 0.04)
    trades, equity = [], []

    for i in range(start_idx, len(klines)):
        hist = klines[: i + 1]
        sig = vol_signals(hist, True, params)
        if not sig:
            continue
        px, mb, ms = sig["px"], sig["buy"], sig["sell"]
        hi = max(b["high"] for b in hist[-5:])
        if hi >= params["R67"] * 0.985 and px < params["R67"] * 0.995:
            r67_fail += 1
        else:
            r67_fail = max(0, r67_fail - 1)
        if r67_fail >= params.get("r67_fail_need", 3) and px >= params.get("r67_px_min", 62):
            ms -= 2 if not sig["uptrend"] else 1

        total = cash + shares * px
        pos_pct = (shares * px / total) if total > 0 else 0.0
        tgt, action = merge_target_v8(mb, ms, params, sig["uptrend"])
        equity.append(total)
        if tgt is None:
            continue
        if abs(pos_pct - tgt) < rebal_min and shares > 0:
            continue
        if tgt == 0 and shares == 0:
            continue
        if not (abs(last_target - tgt) >= rebal_min or (tgt == 0 and shares > 0) or (tgt > 0 and shares == 0)):
            continue
        shares = total * tgt / px
        cash = total - shares * px
        last_target = tgt
        trades.append({"date": klines[i]["date"], "px": px, "tgt": tgt, "action": action})

    final = cash + shares * klines[-1]["close"]
    equity.append(final)
    return (final - 1) * 100, trades, max_drawdown(equity)


def backtest_v9(jh, hh, params, start_idx=21, overnight=True):
    cash, shares = 1.0, 0.0
    r67_fail, last_target = 0, -1.0
    core_on, t_sleeve = False, T_MAX
    last_t_day = -999
    rebal_min = params.get("REBAL_MIN", 0.015)
    trades, equity = [], []

    for i in range(start_idx, len(jh)):
        jh_hist, hh_hist = jh[: i + 1], hh[: i + 1]
        sig = vol_signals(jh_hist, True, params)
        if not sig:
            continue
        px, mb, ms = sig["px"], sig["buy"], sig["sell"]
        hi = max(b["high"] for b in jh_hist[-5:])
        if hi >= params["R67"] * 0.985 and px < params["R67"] * 0.995:
            r67_fail += 1
        else:
            r67_fail = max(0, r67_fail - 1)
        if r67_fail >= 3 and px >= 62:
            ms -= 2 if not sig["uptrend"] else 1

        core_tgt, core_on = core_target_v9(mb, ms, sig, core_on, fast_entry=(i == start_idx))
        prev_t = t_sleeve
        if overnight:
            new_t = hh_t_sleeve(hh_hist, jh_hist, t_sleeve, jh_sig=sig, last_t_day=last_t_day, day_idx=i)
            if new_t != t_sleeve:
                t_sleeve = new_t
                last_t_day = i
        else:
            t_sleeve = hh_t_sleeve_legacy(hh_hist, jh_hist, t_sleeve)
        if core_tgt <= 0:
            tgt, action = 0.0, "空仓"
        elif i == start_idx:
            tgt, action = 1.0, "首日满仓"
        else:
            tgt = min(core_tgt + t_sleeve, 1.0)
            action = "底{:.0%}+T{:.0%}".format(core_tgt, t_sleeve)

        total = cash + shares * px
        pos_pct = (shares * px / total) if total > 0 else 0.0
        equity.append(total)
        if abs(pos_pct - tgt) < rebal_min and shares > 0:
            continue
        if tgt == 0 and shares == 0:
            continue
        if not (abs(last_target - tgt) >= rebal_min or (tgt == 0 and shares > 0) or (tgt > 0 and shares == 0)):
            continue
        shares = total * tgt / px
        cash = total - shares * px
        last_target = tgt
        trades.append({"date": jh[i]["date"], "px": px, "tgt": tgt, "core": core_tgt, "t": t_sleeve, "action": action})

    final = cash + shares * jh[-1]["close"]
    equity.append(final)
    return (final - 1) * 100, trades, max_drawdown(equity)


def _ohlc_path(bar):
    """日K → 日内价格路径 (模拟 tick)"""
    op, hi, lo, cl = bar["open"], bar["high"], bar["low"], bar["close"]
    if cl >= op:
        anchors = [op, lo, lo + (hi - lo) * 0.35, hi, hi - (hi - cl) * 0.4, cl]
    else:
        anchors = [op, hi, hi - (hi - lo) * 0.35, lo, lo + (cl - lo) * 0.4, cl]
    out = []
    steps = 8
    for i in range(steps):
        t = i / (steps - 1)
        seg = t * (len(anchors) - 1)
        j = min(int(seg), len(anchors) - 2)
        frac = seg - j
        px = anchors[j] * (1 - frac) + anchors[j + 1] * frac
        hhmm = 930 + int(t * 330)  # 约 9:30 → 14:30
        if hhmm > 1130 and hhmm < 1300:
            hhmm += 90
        out.append({"time": "{:04d}".format(min(hhmm, 1500)), "price": px})
    return out


def _intraday_from_ticks(ticks, pre_close):
    """由 tick 路径构造 intraday_t_logic 所需字段"""
    prices = [t["price"] for t in ticks]
    px = prices[-1]
    op = prices[0]
    hi, lo = max(prices), min(prices)
    prev = prices[-2] if len(prices) >= 2 else px
    vwap = sum(prices) / len(prices)
    return {
        "price": px,
        "open": op,
        "high": hi,
        "low": lo,
        "pre_close": pre_close,
        "vwap": vwap,
        "prev_price": prev,
        "intraday_pct": (px - op) / op if op else 0.0,
        "pullback_from_high": (hi - px) / hi if hi else 0.0,
        "bounce_from_low": (px - lo) / lo if lo else 0.0,
        "ticks": [{"time": t["time"], "price": t["price"]} for t in ticks],
        "last_time": ticks[-1]["time"],
        "change_pct": (px - pre_close) / pre_close * 100 if pre_close else 0.0,
    }


def backtest_v10(jh, hh, params, start_idx=21):
    """v10 日内T：日K模拟分时路径 + 华虹分钟评分"""
    cash, shares = 1.0, 0.0
    r67_fail, last_target = 0, -1.0
    core_on, t_sleeve = False, T_MAX
    rebal_min = params.get("REBAL_MIN", 0.015)
    min_tick_gap = INTRADAY_T.get("min_tick_gap", 4)
    trades, equity = [], []

    for i in range(start_idx, len(jh)):
        jh_hist, hh_hist = jh[: i + 1], hh[: i + 1]
        sig = vol_signals(jh_hist, True, params)
        if not sig:
            continue

        px_day, mb, ms = sig["px"], sig["buy"], sig["sell"]
        hi = max(b["high"] for b in jh_hist[-5:])
        if hi >= params["R67"] * 0.985 and px_day < params["R67"] * 0.995:
            r67_fail += 1
        else:
            r67_fail = max(0, r67_fail - 1)
        if r67_fail >= 3 and px_day >= 62:
            ms -= 2 if not sig["uptrend"] else 1

        core_tgt, core_on = core_target_v9(mb, ms, sig, core_on, fast_entry=(i == start_idx))
        if core_tgt <= 0:
            t_sleeve = T_MAX

        jh_pre = jh_hist[-2]["close"] if len(jh_hist) >= 2 else jh_hist[-1]["open"]
        hh_pre = hh_hist[-2]["close"] if len(hh_hist) >= 2 else hh_hist[-1]["open"]
        jh_path = _ohlc_path(jh_hist[-1])
        hh_path = _ohlc_path(hh_hist[-1])

        last_t_change = -999
        day_trades = 0

        for k in range(len(jh_path)):
            jh_ticks = jh_path[: k + 1]
            hh_ticks = hh_path[: k + 1]
            jh_state = _intraday_from_ticks(jh_ticks, jh_pre)
            hh_state = _intraday_from_ticks(hh_ticks, hh_pre)

            score, _, _ = score_intraday_hh(hh_state, jh_state)
            new_t, t_act = t_pct_from_intraday_score(
                score, prev_t=t_sleeve, last_time=hh_state["last_time"], uptrend=sig["uptrend"],
            )

            if i == start_idx and k == 0:
                tgt = 1.0
                action = "首日满仓"
            elif core_tgt <= 0:
                tgt, action = 0.0, "空仓"
            else:
                tgt = min(core_tgt + new_t, 1.0)
                action = "底{:.0%}+T{:.0%}".format(core_tgt, new_t)

            px = jh_state["price"]
            total = cash + shares * px
            pos_pct = (shares * px / total) if total > 0 else 0.0

            t_changed = new_t != t_sleeve and (k - last_t_change) >= min_tick_gap
            if t_changed:
                t_sleeve = new_t
                last_t_change = k

            if abs(pos_pct - tgt) < rebal_min and shares > 0:
                continue
            if tgt == 0 and shares == 0:
                continue
            if not (abs(last_target - tgt) >= rebal_min or (tgt == 0 and shares > 0) or (tgt > 0 and shares == 0)):
                continue

            shares = total * tgt / px
            cash = total - shares * px
            last_target = tgt
            day_trades += 1
            trades.append({
                "date": jh[i]["date"],
                "time": hh_state["last_time"],
                "px": px,
                "tgt": tgt,
                "core": core_tgt,
                "t": t_sleeve,
                "action": action,
                "score": score,
            })

        close_px = jh_hist[-1]["close"]
        total = cash + shares * close_px
        equity.append(total)

    final = cash + shares * jh[-1]["close"]
    if not equity or equity[-1] != final:
        equity.append(final)
    return (final - 1) * 100, trades, max_drawdown(equity)


def slice_year(klines, days=252):
    if len(klines) <= days:
        return klines, 21
    return klines[-days:], 21


def main():
    parser = argparse.ArgumentParser(description="晶合688249 本地回测")
    parser.add_argument("--days", type=int, default=252, help="回测交易日数(默认252≈1年)")
    parser.add_argument("--online", action="store_true", help="在线拉取东财数据")
    args = parser.parse_args()

    if args.online:
        jh_raw, hh_raw, src = fetch_online(days=max(args.days + 30, 280))
        jh, hh = align_klines(jh_raw, hh_raw)
    else:
        cache_jh = os.path.join("data", "688249_daily_sina.json")
        cache_hh = os.path.join("data", "688347_daily.json")
        if os.path.isfile(cache_jh) and os.path.isfile(cache_hh):
            with open(cache_jh, encoding="utf-8") as f:
                jh_raw = json.load(f)["klines"]
            with open(cache_hh, encoding="utf-8") as f:
                hh_raw = json.load(f)["klines"]
            src = "cache"
        else:
            jh_raw, hh_raw, src = fetch_online(days=max(args.days + 30, 280))
        jh, hh = align_klines(jh_raw, hh_raw)

    jh, start = slice_year(jh, args.days)
    hh = hh[-len(jh):]

    start_px = jh[start]["close"]
    end_px = jh[-1]["close"]
    bh = (end_px / start_px - 1) * 100

    v8_params = copy.deepcopy(BASE_PARAMS)
    r8, t8, mdd8 = backtest_v8(jh, v8_params, start)
    r9, t9, mdd9 = backtest_v9(jh, hh, v8_params, start, overnight=True)
    r93, t93, mdd93 = backtest_v9(jh, hh, v8_params, start, overnight=False)
    r10, t10, mdd10 = backtest_v10(jh, hh, v8_params, start)
    rt_n, rt_win, rt_rows = t_roundtrip_success(t9)

    print("=" * 60)
    print("  晶合688249 回测报告 (约 {} 个交易日)".format(len(jh) - start))
    print("  数据源: {}".format(src))
    print("  区间: {} ({:.2f}) -> {} ({:.2f})".format(
        jh[start]["date"], start_px, jh[-1]["date"], end_px))
    print("  股价涨幅: {:+.1f}%".format(bh))
    print("=" * 60)
    print("")
    print("{:<20} {:>10} {:>10} {:>8}".format("策略", "收益率", "最大回撤", "交易笔数"))
    print("-" * 52)
    print("{:<20} {:>9.1f}% {:>10} {:>8}".format("买入持有", bh, "-", 0))
    print("{:<20} {:>9.1f}% {:>9.1f}% {:>8}".format("v8.0 趋势", r8, mdd8, len(t8)))
    print("{:<20} {:>9.1f}% {:>9.1f}% {:>8}".format("v11 隔日T", r9, mdd9, len(t9)))
    print("{:<20} {:>9.1f}% {:>9.1f}% {:>8}".format("v9.3 隔日T(旧)", r93, mdd93, len(t93)))
    print("{:<20} {:>9.1f}% {:>9.1f}% {:>8}".format("v10.1 日内T(模拟)", r10, mdd10, len(t10)))
    print("")
    print("  v11: 隔日T min_days={} | 华虹信号可隔夜".format(OVERNIGHT_T.get("min_days", 0)))
    print("  v11 T回补成功率: {:.1f}% ({}/{})".format(rt_win, int(round(rt_win * rt_n / 100)) if rt_n else 0, rt_n))
    if OVERNIGHT_T.get("target_success_rate"):
        print("  目标成功率: {}%".format(OVERNIGHT_T["target_success_rate"]))
    print("")
    print("--- v10.1 末8笔 ---")
    for t in t10[-8:]:
        print("  {} {} px={:.2f} 总={:.0%} score={} ({})".format(
            t["date"], t.get("time", ""), t["px"], t["tgt"], t.get("score", ""), t["action"]))
    print("")
    print("--- v11 隔日T 全部交易 ---")
    for t in t9:
        print("  {} px={:.2f} 总={:.0%} ({})".format(t["date"], t["px"], t["tgt"], t["action"]))
    if rt_rows:
        print("")
        print("--- v11 T回补明细 ---")
        for r in rt_rows:
            flag = "✓" if r["ok"] else "✗"
            print("  {} {}@{:.2f} -> {}@{:.2f} spread={:+.1f}%".format(
                flag, r["sell_date"], r["sell_px"], r["buy_date"], r["buy_px"], r["spread_pct"]))

    print("")
    print("--- v9.3 隔日T(旧) 交易 ---")
    for t in t93:
        print("  {} px={:.2f} 总={:.0%} ({})".format(t["date"], t["px"], t["tgt"], t["action"]))
    print("=" * 60)


if __name__ == "__main__":
    main()
