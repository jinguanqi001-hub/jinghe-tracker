# -*- coding: utf-8 -*-
"""晶合集成量化信号引擎 — 融合基本面事件与量价规则"""

from datetime import datetime

from config import H_SHARE, LEVELS, THRESHOLDS


def _sig(level, category, message, action):
    return {"level": level, "category": category, "message": message, "action": action}


def estimate_ah_premium(a_price_cny):
    h_mid = (H_SHARE["price_low_hkd"] + H_SHARE["price_high_hkd"]) / 2
    h_cny = h_mid * H_SHARE["hkd_cny_rate"]
    if h_cny <= 0:
        return None, None
    premium = (a_price_cny - h_cny) / h_cny
    return premium, h_cny


def days_to_h_listing():
    try:
        listing = datetime.strptime(H_SHARE["listing_date"], "%Y-%m-%d").date()
        return (listing - datetime.now().date()).days
    except Exception:
        return None


def evaluate(klines, indicators, realtime=None):
    signals = []
    latest = indicators["latest"]
    prev = indicators["prev"]
    close = latest["close"]
    cm = indicators["candle"]

    # ── 价位监控 ──
    for name, price in LEVELS.items():
        dist = (close - price) / price
        if abs(dist) < 0.015:
            signals.append(
                _sig("INFO", "价位", "收盘价接近关键位 {} ({:.2f}元)".format(name, price), "观察该位置攻防")
            )
        elif close < price and name in ("platform_support", "breakout_base", "limit_up_support"):
            # 跌破支撑需阴线确认，避免放量反弹日误报
            if close < price * 0.99 and cm["is_bearish"]:
                signals.append(
                    _sig("SELL", "支撑", "阴线跌破 {} 支撑 {:.2f}元 (现 {:.2f})".format(name, price, close), "减仓")
                )

    # ── 67 元三重顶 ──
    if latest["high"] >= LEVELS["strong_resistance"] * 0.98 and close < LEVELS["strong_resistance"]:
        signals.append(
            _sig(
                "SELL",
                "形态",
                "冲高 {:.2f} 未能站稳 {:.0f} 压力区 (收 {:.2f})".format(
                    latest["high"], LEVELS["strong_resistance"], close
                ),
                "分批止盈",
            )
        )
    if indicators["resistance_67_tests"] >= 3 and close >= 62.0:
        signals.append(
            _sig(
                "SELL",
                "形态",
                "近10日 {} 次测试67元失败 — 三重顶风险".format(indicators["resistance_67_tests"]),
                "优先减仓",
            )
        )
    elif indicators["resistance_67_tests"] >= 2 and close < 62.0:
        signals.append(
            _sig(
                "WARN",
                "形态",
                "近10日 {} 次测试67元失败 — 关注压力".format(indicators["resistance_67_tests"]),
                "观察",
            )
        )

    # ── 长上影 / 射击之星 ──
    if cm["upper_shadow_ratio"] >= THRESHOLDS["upper_shadow_ratio"] and latest["turnover_pct"] >= THRESHOLDS["volume_normal_turnover"]:
        signals.append(
            _sig(
                "SELL",
                "K线",
                "长上影线 (上影/实体比 {:.1f}) + 换手 {:.2f}%".format(
                    cm["upper_shadow_ratio"], latest["turnover_pct"]
                ),
                "高位派发信号",
            )
        )

    # ── 天量滞涨 ──
    if latest["turnover_pct"] >= THRESHOLDS["volume_climax_turnover"]:
        if latest["change_pct"] <= 0 or cm["upper_shadow"] > cm["body"]:
            signals.append(
                _sig(
                    "SELL",
                    "量能",
                    "天量滞涨: 换手 {:.2f}% 涨幅 {:.2f}%".format(
                        latest["turnover_pct"], latest["change_pct"]
                    ),
                    "经典出货量",
                )
            )
        else:
            signals.append(
                _sig("WARN", "量能", "换手率 {:.2f}% 达高潮区 — 警惕变盘".format(latest["turnover_pct"]), "不追高")
            )

    # ── 放量长阴 ──
    if latest["change_pct"] <= -5 and latest["turnover_pct"] >= 3.5:
        signals.append(
            _sig(
                "SELL",
                "K线",
                "放量长阴 {:.2f}% (换手 {:.2f}%)".format(latest["change_pct"], latest["turnover_pct"]),
                "参考5/21出货模式 — 减仓",
            )
        )

    # ── 均线 ──
    ma5, ma10, ma20 = indicators["ma5"], indicators["ma10"], indicators["ma20"]
    if ma5 and close < ma5 and prev["close"] >= ma5:
        signals.append(_sig("SELL", "趋势", "跌破5日均线 ({:.2f})".format(ma5), "短线转弱"))
    if ma10 and close < ma10 and prev["close"] >= ma10:
        signals.append(_sig("WARN", "趋势", "跌破10日均线 ({:.2f})".format(ma10), "考虑减仓"))
    if indicators["deviation_ma20"] and indicators["deviation_ma20"] > THRESHOLDS["ma_deviation_warning"]:
        signals.append(
            _sig(
                "WARN",
                "估值",
                "偏离20日线 +{:.1f}% — 超涨".format(indicators["deviation_ma20"] * 100),
                "不宜追高",
            )
        )

    # ── RSI ──
    rsi_val = indicators["rsi"]
    if rsi_val:
        if rsi_val >= THRESHOLDS["rsi_overbought"]:
            signals.append(_sig("WARN", "动量", "RSI {:.1f} 超买区".format(rsi_val), "警惕回调"))
        elif rsi_val <= THRESHOLDS["rsi_oversold"]:
            signals.append(_sig("BUY", "动量", "RSI {:.1f} 超卖区".format(rsi_val), "可关注反弹"))

    # ── MACD ──
    macd = indicators["macd"]
    if macd and macd["hist"] < 0 and macd["hist_prev"] >= 0:
        signals.append(_sig("SELL", "动量", "MACD 柱由正转负", "动量衰减"))
    elif macd and macd["hist"] > 0 and macd["hist_prev"] <= 0:
        signals.append(_sig("BUY", "动量", "MACD 柱由负转正", "动量修复"))

    # ── 利好出尽 (类似6/1) ──
    if latest["change_pct"] <= -5 and 41 <= close <= 45:
        signals.append(_sig("WARN", "事件", "42-45元区大幅下跌 — 利好出尽模式", "观望"))

    # ── H股 / A-H 溢价 ──
    premium, h_cny = estimate_ah_premium(close)
    days_h = days_to_h_listing()
    if premium is not None and premium >= THRESHOLDS["ah_premium_warning"]:
        signals.append(
            _sig(
                "SELL",
                "事件",
                "A/H溢价 {:.0f}% (A {:.2f} vs H≈{:.2f}元) — 收敛风险".format(premium * 100, close, h_cny),
                "H股上市前分批减仓",
            )
        )
    if days_h is not None and 0 <= days_h <= 7:
        signals.append(
            _sig(
                "WARN",
                "事件",
                "距H股上市还有 {} 天 ({})".format(days_h, H_SHARE["listing_date"]),
                "历史经验: 上市前后A股易波动",
            )
        )

    # ── 买入/持有 ──
    if ma5 and ma10 and ma20 and close > ma5 > ma10 > ma20 and rsi_val and 50 <= rsi_val <= 65:
        if not any(s["level"] == "SELL" for s in signals):
            signals.append(_sig("BUY", "趋势", "均线多头排列 + RSI健康", "可持有"))

    if ma10 and prev["close"] < ma10 and close > ma10 and not cm["is_bearish"]:
        signals.append(_sig("BUY", "形态", "V型反转 — 放量站回MA10", "可加仓"))

    if ma20 and close > ma20 and ma5 > ma10 > ma20:
        low = latest["low"]
        if low <= ma20 * 1.015 and close > ma20:
            signals.append(_sig("BUY", "趋势", "MA20回踩企稳", "趋势中加仓"))

    if 24 <= close <= 28:
        signals.append(_sig("BUY", "价位", "回落至24-28元建仓区", "可考虑分批建仓"))

    # 综合评分
    score = sum({"BUY": 1, "INFO": 0, "WARN": -1, "SELL": -2}[s["level"]] for s in signals)
    if score <= -4:
        verdict = "强烈减仓"
    elif score <= -2:
        verdict = "偏空 · 建议减仓"
    elif score >= 2:
        verdict = "偏多 · 可持有/建仓"
    else:
        verdict = "中性 · 观望"

    return {"signals": signals, "score": score, "verdict": verdict, "ah_premium": premium, "h_price_cny": h_cny}
