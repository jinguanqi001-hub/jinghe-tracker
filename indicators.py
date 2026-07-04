# -*- coding: utf-8 -*-
"""技术指标计算（纯 Python，兼容 Python 3.7+）"""

from config import THRESHOLDS


def sma(values, period):
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def ema_series(values, period):
    if not values:
        return []
    k = 2.0 / (period + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def rsi(closes, period=None):
    period = period or THRESHOLDS["rsi_period"]
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def macd(closes, fast=12, slow=26, signal=9):
    if len(closes) < slow + signal:
        return None
    ema_fast = ema_series(closes, fast)
    ema_slow = ema_series(closes, slow)
    dif = [f - s for f, s in zip(ema_fast, ema_slow)]
    dea = ema_series(dif, signal)
    hist = [d - e for d, e in zip(dif, dea)]
    return {"dif": dif[-1], "dea": dea[-1], "hist": hist[-1], "hist_prev": hist[-2] if len(hist) > 1 else 0}


def bollinger(closes, period=20, num_std=2):
    if len(closes) < period:
        return None
    window = closes[-period:]
    mid = sum(window) / period
    var = sum((x - mid) ** 2 for x in window) / period
    std = var ** 0.5
    return {"upper": mid + num_std * std, "mid": mid, "lower": mid - num_std * std}


def candle_metrics(bar):
    """单根 K 线形态指标"""
    o, h, l, c = bar["open"], bar["high"], bar["low"], bar["close"]
    body = abs(c - o)
    upper_shadow = h - max(o, c)
    lower_shadow = min(o, c) - l
    full_range = h - l if h > l else 0.0001
    return {
        "body": body,
        "upper_shadow": upper_shadow,
        "lower_shadow": lower_shadow,
        "upper_shadow_ratio": upper_shadow / body if body > 0.01 else upper_shadow / full_range,
        "is_bearish": c < o,
        "is_bullish": c > o,
        "full_range": full_range,
    }


def resistance_test_count(klines, level, tolerance=0.02, lookback=10):
    """统计近 lookback 日内接近 level 但未有效突破的次数"""
    count = 0
    for bar in klines[-lookback:]:
        near = bar["high"] >= level * (1 - tolerance) and bar["close"] < level
        if near:
            count += 1
    return count


def compute_all(klines):
    closes = [b["close"] for b in klines]
    volumes = [b["volume"] for b in klines]
    turnovers = [b["turnover_pct"] for b in klines]

    ma5 = sma(closes, THRESHOLDS["ma_short"])
    ma10 = sma(closes, THRESHOLDS["ma_mid"])
    ma20 = sma(closes, THRESHOLDS["ma_long"])

    latest = klines[-1]
    prev = klines[-2] if len(klines) > 1 else latest
    cm = candle_metrics(latest)

    deviation_ma20 = None
    if ma20 and ma20 > 0:
        deviation_ma20 = (latest["close"] - ma20) / ma20

    vol_ma5 = sma(volumes, 5)
    vol_ratio = latest["volume"] / vol_ma5 if vol_ma5 else 1.0

    return {
        "latest": latest,
        "prev": prev,
        "ma5": ma5,
        "ma10": ma10,
        "ma20": ma20,
        "rsi": rsi(closes),
        "macd": macd(closes),
        "boll": bollinger(closes),
        "candle": cm,
        "deviation_ma20": deviation_ma20,
        "vol_ratio": vol_ratio,
        "avg_turnover_5d": sma(turnovers, 5),
        "resistance_67_tests": resistance_test_count(klines, 67.0),
    }
