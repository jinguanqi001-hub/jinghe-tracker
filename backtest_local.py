#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地回测：复现 SuperMind 策略逻辑并对比改进版"""

import json
import copy


def load_klines(path="data/688249_daily_ths.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f)["klines"]


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

    px = c[-1]
    hi = h[-1]
    lo = l[-1]
    op = o[-1]
    prev = c[-2]
    prev2 = c[-3]

    ma5 = sum(c[-5:]) / 5
    ma10 = sum(c[-10:]) / 10
    ma20 = sum(c[-20:]) / 20
    rsi_v = rsi(c)

    vma5 = sum(v[-6:-1]) / 5 if len(v) >= 6 else float(v[-1] or 1)
    if vma5 <= 0:
        vma5 = 1.0
    vr = float(v[-1] or 0) / vma5
    denom = sum(v[-7:-2]) / 5 if len(v) >= 7 else vma5
    if denom <= 0:
        denom = 1.0
    vr_prev = float(v[-2] or 0) / denom

    body = abs(px - op) if abs(px - op) > 0.01 else 0.01
    upper = (hi - max(op, px)) / body
    chg = (px - prev) / prev if prev else 0.0

    R67, R61, S58, S52 = params["R67"], params["R61"], params["S58"], params["S52"]
    VOL_BREAK = params["VOL_BREAK"]
    VOL_STRONG = params["VOL_STRONG"]
    VOL_CLIMAX = params["VOL_CLIMAX"]
    VOL_PANIC = params["VOL_PANIC"]
    SHADOW_RATIO = params["SHADOW_RATIO"]

    buy = sell = 0
    uptrend = px > ma20 and ma5 > ma10 > ma20

    if use_levels:
        if px > S58 and prev <= S58 * 1.005 and vr >= VOL_BREAK:
            buy += 3
        if px > S52 and prev2 <= S52 * 1.01 and prev > S52 * 0.995 and vr >= VOL_BREAK:
            buy += 2
        if px >= R61 * 0.98 and vr >= VOL_STRONG and upper >= 0.35:
            sell -= 2 if not uptrend else 1
        if hi >= R67 * 0.985 and px < R67 * 0.992 and vr >= VOL_BREAK:
            sell -= 3 if not uptrend else 1
        # 破位需阴线确认，避免放量反弹日误杀
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

    # V型反转 / 动量加速
    if params.get("recovery_buy"):
        ret5 = (px - c[-6]) / c[-6] if len(c) >= 6 and c[-6] else 0.0
        if prev < ma10 and px > ma10 and px > op and vr >= VOL_BREAK:
            buy += params.get("recovery_buy_score", 4)
        if ret5 >= params.get("momentum_ret5", 0.12) and px > ma5 and px > op:
            buy += params.get("momentum_buy_score", 3)

    if params.get("ma20_pullback") and uptrend and lo <= ma20 * 1.015 and px > ma20 and px > op:
        buy += params.get("ma20_pullback_score", 2)

    if vr >= VOL_CLIMAX and upper >= SHADOW_RATIO:
        sell -= 3 if not uptrend else 1
    if vr >= VOL_CLIMAX and px < op:
        sell -= 3 if not uptrend else 2
    if vr >= VOL_CLIMAX and abs(chg) < 0.008:
        sell -= 2 if not uptrend else 1
    if px < ma10 and prev >= ma10 and px < op and vr >= VOL_PANIC:
        sell -= 2
    if px < ma20 and prev < ma20 and px < op and vr >= VOL_PANIC:
        sell -= 4
    rsi_sell = params.get("rsi_sell", 78)
    if rsi_v >= rsi_sell and vr >= VOL_STRONG:
        sell -= 1 if not uptrend else 0

    return {
        "buy": buy,
        "sell": sell,
        "px": px,
        "ma5": ma5,
        "ma10": ma10,
        "ma20": ma20,
        "vr": vr,
        "uptrend": uptrend,
        "rsi": rsi_v,
    }


def merge_target(mb, ms, hold, params, uptrend=False):
    # 强买时优先，避免被轻微卖信号压仓
    if mb >= 3 and ms > -4:
        if uptrend:
            return params.get("pos_max", 0.98), "趋势强买"
        return params.get("pos_strong", 0.95), "强买"

    if params.get("trend_hold") and uptrend and ms > params.get("trend_sell_floor", -4):
        if mb >= 1:
            return params.get("pos_max", 0.98), "趋势强持"
        if ms <= -1:
            return max(params.get("trend_min_pos", 0.80), 0.80), "趋势减仓"
        return params.get("trend_min_pos", 0.85), "趋势持有"

    if ms <= -8:
        return 0.0, "清仓"
    if ms <= -6:
        return params.get("pos_heavy_cut", 0.35), "重度减仓"
    if ms <= -3:
        return params.get("pos_light_cut", 0.65), "轻度减仓"
    if mb >= 4:
        return params.get("pos_max", 0.98), "强买"
    if mb >= 2:
        return 0.85, "买入加仓"
    if mb >= 1:
        return 0.80, "偏多持有"
    if mb + ms <= -2:
        return 0.55, "偏空降仓"
    return None, "观望"


def backtest(klines, params, start_idx=21):
    cash = 1.0
    shares = 0.0
    r67_fail = 0
    last_target = -1.0
    rebal_min = params.get("REBAL_MIN", 0.08)
    trades = []

    for i in range(start_idx, len(klines)):
        hist = klines[: i + 1]
        sig = vol_signals(hist, True, params)
        if not sig:
            continue

        px = sig["px"]
        mb, ms = sig["buy"], sig["sell"]

        recent = hist[-5:]
        hi = max(b["high"] for b in recent)
        if hi >= params["R67"] * 0.985 and px < params["R67"] * 0.995:
            r67_fail += 1
        else:
            r67_fail = max(0, r67_fail - 1)

        r67_need = params.get("r67_fail_need", 2)
        r67_px_min = params.get("r67_px_min", 59.0)
        if r67_fail >= r67_need and px >= r67_px_min:
            ms -= 2 if not sig["uptrend"] else 1

        hold = shares
        total = cash + shares * px
        pos_pct = (shares * px / total) if total > 0 else 0.0

        tgt, action = merge_target(mb, ms, hold, params, sig["uptrend"])
        if tgt is None:
            continue

        if abs(pos_pct - tgt) < rebal_min and hold > 0:
            continue
        if tgt == 0.0 and hold == 0:
            continue
        if not (abs(last_target - tgt) >= rebal_min or (tgt == 0 and hold > 0) or (tgt > 0 and hold == 0)):
            continue

        target_value = total * tgt
        target_shares = target_value / px
        delta = target_shares - shares
        if abs(delta) * px / total < 0.01:
            continue

        shares = target_shares
        cash = total - shares * px
        last_target = tgt
        trades.append({"date": klines[i]["date"], "px": px, "tgt": tgt, "action": action, "mb": mb, "ms": ms})

    final = cash + shares * klines[-1]["close"]
    ret = (final - 1.0) * 100
    return ret, trades, shares > 0


def main():
    klines = load_klines()
    bh = (klines[-1]["close"] / klines[21]["close"] - 1) * 100

    base_params = {
        "R67": 67.0, "R61": 61.0, "S58": 58.0, "S52": 52.0,
        "VOL_BREAK": 1.30, "VOL_STRONG": 1.55, "VOL_CLIMAX": 1.90,
        "VOL_PANIC": 1.45, "SHADOW_RATIO": 0.50,
        "REBAL_MIN": 0.08, "r67_fail_need": 2, "r67_px_min": 59.0,
        "rsi_sell": 78,
    }

    v8_params = copy.deepcopy(base_params)
    v8_params.update({
        "REBAL_MIN": 0.05,
        "r67_fail_need": 3,
        "r67_px_min": 62.0,
        "rsi_sell": 85,
        "ma20_pullback": True,
        "ma20_pullback_score": 3,
        "recovery_buy": True,
        "recovery_buy_score": 4,
        "momentum_ret5": 0.12,
        "momentum_buy_score": 3,
        "trend_hold": True,
        "trend_min_pos": 0.88,
        "trend_sell_floor": -5,
        "pos_max": 0.98,
        "pos_strong": 0.95,
        "pos_light_cut": 0.70,
        "pos_heavy_cut": 0.40,
    })

    r1, t1, _ = backtest(klines, base_params)
    r2, t2, _ = backtest(klines, v8_params)

    print(f"区间: {klines[21]['date']} -> {klines[-1]['date']}")
    print(f"买入持有: {bh:.1f}%")
    print(f"v7.2 模拟: {r1:.1f}%  交易 {len(t1)} 笔")
    print(f"v8.0 模拟: {r2:.1f}%  交易 {len(t2)} 笔")
    print("\n--- v7.2 末5笔 ---")
    for t in t1[-5:]:
        print(t)
    print("\n--- v8.0 末5笔 ---")
    for t in t2[-5:]:
        print(t)


if __name__ == "__main__":
    main()
