# -*- coding: utf-8 -*-
"""报告格式化输出"""

LEVEL_ICON = {"BUY": "🟢", "INFO": "🔵", "WARN": "🟡", "SELL": "🔴"}


def fmt_price(v):
    return "{:.2f}".format(v) if v is not None else "-"


def fmt_pct(v):
    return "{:+.2f}%".format(v) if v is not None else "-"


def render_compare(compare_result):
    lines = []
    lines.append("")
    lines.append("【双源对比】同花顺 vs 东方财富")
    rt = compare_result.get("realtime") or {}
    ths = rt.get("ths") or {}
    em = rt.get("eastmoney") or {}
    lines.append("  现价:  同花顺 {}  |  东财 {}  |  价差 {} ({:+.2f}%)".format(
        fmt_price(ths.get("price")),
        fmt_price(em.get("price")),
        fmt_price(rt.get("price_diff")),
        rt.get("price_diff_pct") or 0,
    ))
    lines.append("  涨跌:  同花顺 {}  |  东财 {}".format(
        fmt_pct(ths.get("change_pct")),
        fmt_pct(em.get("change_pct")),
    ))
    lines.append("  换手:  同花顺 {}%  |  东财 {}%".format(
        fmt_price(ths.get("turnover_pct")),
        fmt_price(em.get("turnover_pct")),
    ))
    k = compare_result.get("klines") or {}
    if k.get("rows"):
        lines.append("  近{}日收盘最大偏差: {:.2f}%".format(k.get("days", 0), k.get("max_close_diff_pct", 0)))
    status = "一致 ✓" if rt.get("consistent") else "存在差异 ⚠"
    lines.append("  数据一致性: {}".format(status))
    for a in rt.get("alerts") or []:
        icon = LEVEL_ICON.get(a.get("level"), "⚪")
        lines.append("  {} {}".format(icon, a.get("message")))
    return "\n".join(lines)


def render_iwencai(iwencai_result):
    lines = []
    lines.append("")
    lines.append("【问财联动】")
    lines.append("  问句: {}".format(iwencai_result.get("query", "")))
    lines.append("  状态: {}".format(iwencai_result.get("message", "")))
    fields = iwencai_result.get("fields") or {}
    if fields:
        lines.append("  关键字段:")
        shown = 0
        for k, v in fields.items():
            if shown >= 12:
                lines.append("  ... (共 {} 项)".format(len(fields)))
                break
            lines.append("    {}: {}".format(k, v))
            shown += 1
    lines.append("  链接: {}".format(iwencai_result.get("url", "")))
    return "\n".join(lines)


def render_t_trading(t_result):
    if not t_result:
        return ""
    lines = []
    lines.append("")
    lines.append("【仓位结构 v9】75%底仓 + 25%做T (基准: {})".format(t_result.get("benchmark", "华虹公司")))
    if t_result.get("error"):
        lines.append("  ⚠ 华虹数据: {}".format(t_result["error"]))
        return "\n".join(lines)
    lines.append("  华虹现价: {}  涨跌: {}%  RSI: {}".format(
        fmt_price(t_result.get("benchmark_price")),
        fmt_price(t_result.get("benchmark_change_pct")),
        fmt_price(t_result.get("benchmark_rsi")),
    ))
    lines.append("  底仓: {:.0%} (不动)  |  T仓: {:.0%} ({})  |  合计: {:.0%}".format(
        t_result.get("core_pct", 0.75),
        t_result.get("t_pct", 0),
        t_result.get("t_action", ""),
        t_result.get("total_pct", 0),
    ))
    if t_result.get("bull_lock"):
        lines.append("  🔒 趋势锁满 — 75%底仓+25%T = 100%")
    for s in t_result.get("signals") or []:
        icon = LEVEL_ICON.get(s["level"], "⚪")
        lines.append("  {} {} → {}".format(icon, s["message"], s["action"]))
    return "\n".join(lines)


def render_report(stock_name, realtime, indicators, evaluation, source_label="", compare_result=None, iwencai_result=None, t_result=None):
    latest = indicators["latest"]
    lines = []
    lines.append("=" * 60)
    lines.append("  {} ({}) 量化跟踪报告".format(stock_name, latest.get("date", "")))
    src = source_label or realtime.get("source", latest.get("source", ""))
    if src:
        lines.append("  数据源: {}".format(src))
    lines.append("  生成时间: {}".format(realtime.get("timestamp", "")))
    lines.append("=" * 60)

    price = realtime.get("price") or latest["close"]
    lines.append("")
    lines.append("【行情快照】")
    lines.append("  现价: {}  涨跌: {}  换手: {}%".format(
        fmt_price(price),
        fmt_pct(realtime.get("change_pct") or latest.get("change_pct")),
        fmt_price(realtime.get("turnover_pct") or latest.get("turnover_pct")),
    ))
    lines.append("  今开: {}  最高: {}  最低: {}  昨收: {}".format(
        fmt_price(realtime.get("open") or latest["open"]),
        fmt_price(realtime.get("high") or latest["high"]),
        fmt_price(realtime.get("low") or latest["low"]),
        fmt_price(realtime.get("pre_close")),
    ))

    lines.append("")
    lines.append("【技术指标】")
    lines.append("  MA5: {}  MA10: {}  MA20: {}".format(
        fmt_price(indicators["ma5"]),
        fmt_price(indicators["ma10"]),
        fmt_price(indicators["ma20"]),
    ))
    lines.append("  RSI(14): {}  量比(5日): {:.2f}x".format(
        fmt_price(indicators["rsi"]),
        indicators["vol_ratio"] or 0,
    ))
    if indicators["deviation_ma20"] is not None:
        lines.append("  偏离MA20: {:+.1f}%".format(indicators["deviation_ma20"] * 100))
    macd = indicators.get("macd")
    if macd:
        lines.append("  MACD: DIF={:.3f} DEA={:.3f} HIST={:.3f}".format(macd["dif"], macd["dea"], macd["hist"]))
    boll = indicators.get("boll")
    if boll:
        lines.append("  BOLL: 上={:.2f} 中={:.2f} 下={:.2f}".format(boll["upper"], boll["mid"], boll["lower"]))

    cm = indicators["candle"]
    lines.append("  上影/实体比: {:.2f}  5日均换手: {}%".format(
        cm["upper_shadow_ratio"],
        fmt_price(indicators["avg_turnover_5d"]),
    ))

    if evaluation.get("ah_premium") is not None:
        lines.append("")
        lines.append("【A/H 溢价】")
        lines.append("  H股参考价: {}元  溢价: {:.0f}%".format(
            fmt_price(evaluation["h_price_cny"]),
            evaluation["ah_premium"] * 100,
        ))

    lines.append("")
    lines.append("【关键价位】")
    from config import LEVELS
    for name, lv in LEVELS.items():
        dist = (price - lv) / lv * 100
        flag = " ← 附近" if abs(dist) < 1.5 else ""
        lines.append("  {:22s} {:.2f}元 ({:+.1f}%){}".format(name, lv, dist, flag))

    lines.append("")
    lines.append("【综合研判】 {}  (评分: {})".format(evaluation["verdict"], evaluation["score"]))
    lines.append("-" * 60)

    if evaluation["signals"]:
        lines.append("【触发信号】")
        for s in evaluation["signals"]:
            icon = LEVEL_ICON.get(s["level"], "⚪")
            lines.append("  {} [{}] {} → {}".format(icon, s["category"], s["message"], s["action"]))
    else:
        lines.append("  暂无触发信号")

    if t_result:
        lines.append(render_t_trading(t_result))

    if compare_result:
        lines.append(render_compare(compare_result))
    if iwencai_result:
        lines.append(render_iwencai(iwencai_result))

    lines.append("=" * 60)
    return "\n".join(lines)


def render_compact(realtime, evaluation):
    price = realtime.get("price", "-")
    return "[688249] 现价:{} | {} | 评分:{}".format(price, evaluation["verdict"], evaluation["score"])
