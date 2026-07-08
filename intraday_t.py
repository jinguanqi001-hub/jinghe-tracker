#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
晶合688249 日内T监控 — 75%底仓 + 25%华虹基准T (分钟级)

用法:
  python3 intraday_t.py              # 单次
  python3 intraday_t.py --watch 60   # 每60秒刷新 (盘中)
  python3 intraday_t.py --json
"""

import argparse
import json
import sys
import time
from datetime import datetime

from config import ALERT_LOG, BENCHMARK, INTRADAY_T, POSITION, STOCK_NAME
from intraday_t_logic import evaluate_intraday_t
from ths_fetcher import fetch_benchmark_intraday, fetch_intraday


def _in_trading_session(last_time):
    """A股交易时段 9:30-11:30, 13:00-15:00"""
    if not last_time or len(last_time) < 4:
        return False
    t = int(last_time[:4])
    return (930 <= t <= 1130) or (1300 <= t <= 1500)


def _log_alert(msg):
    import os
    os.makedirs("data", exist_ok=True)
    line = "[{}] {}\n".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg)
    with open(ALERT_LOG, "a", encoding="utf-8") as f:
        f.write(line)


def _render(result):
    lines = []
    lines.append("=" * 60)
    lines.append("  {} 日内T监控 (v10 分钟级华虹基准)".format(STOCK_NAME))
    lines.append("  时间: {}  tick:{}".format(
        result.get("benchmark_time", "-"),
        result.get("tick_count", "-"),
    ))
    lines.append("=" * 60)
    lines.append("")
    lines.append("【华虹 {}】 现价:{}  涨跌:{}%  日内:{}%  VWAP:{}  RSI:{}".format(
        BENCHMARK["code"],
        result.get("benchmark_price"),
        result.get("benchmark_change_pct"),
        result.get("benchmark_intraday_pct"),
        round(result.get("benchmark_vwap") or 0, 2),
        result.get("benchmark_rsi"),
    ))
    lines.append("【晶合 688249】 现价:{}  日内:{}%".format(
        result.get("jh_price"),
        result.get("jh_intraday_pct"),
    ))
    lines.append("")
    lines.append("【仓位】 底仓 {:.0%} (不动) | T仓 {:.0%} ({}) | 合计 {:.0%}".format(
        result.get("core_pct", POSITION["core_pct"]),
        result.get("t_pct", 0),
        result.get("t_action", ""),
        result.get("total_pct", 0),
    ))
    lines.append("  华虹T评分: {}".format(result.get("score")))
    for n in result.get("signals") or []:
        icon = "🟢" if any(k in n for k in ("回升", "反弹", "超卖", "转强", "晶合强")) else "🔴"
        lines.append("  {} {}".format(icon, n))
    lines.append("=" * 60)
    return "\n".join(lines)


def run_once(prev_t=None, as_json=False):
    try:
        hh = fetch_benchmark_intraday()
        jh = fetch_intraday()
    except Exception as e:
        err = {"error": str(e), "mode": "intraday"}
        if as_json:
            print(json.dumps(err, ensure_ascii=False, indent=2))
        else:
            print("⚠ 分时数据获取失败: {}".format(e), file=sys.stderr)
        return None, prev_t

    if not _in_trading_session(hh.get("last_time")):
        msg = "非交易时段 (最后tick: {})，信号仅供参考".format(hh.get("last_time"))
        if not as_json:
            print("ℹ {}".format(msg))

    result = evaluate_intraday_t(hh, jh, prev_t=prev_t)
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    else:
        print(_render(result))

    return result, result.get("t_pct", prev_t)


def main():
    parser = argparse.ArgumentParser(description="晶合688249 日内T (华虹分钟基准)")
    parser.add_argument("--watch", type=int, metavar="SEC", help="定时刷新(秒)，建议60")
    parser.add_argument("--json", action="store_true", help="JSON输出")
    args = parser.parse_args()

    prev_t = POSITION["t_max_pct"]
    prev_action = None

    if args.watch:
        interval = max(30, args.watch)
        print("日内T监控 · 每 {} 秒刷新 (Ctrl+C 退出)".format(interval))
        print("底仓 {:.0%} + T仓 0~{:.0%} · 基准 {}".format(
            POSITION["core_pct"], POSITION["t_max_pct"], BENCHMARK["name"],
        ))
        print("最短调仓间隔: {}秒\n".format(INTRADAY_T["min_trade_interval_sec"]))
        last_trade_ts = 0

        while True:
            try:
                result, new_t = run_once(prev_t=prev_t, as_json=False)
                if result and result.get("t_action") != prev_action:
                    action = result["t_action"]
                    if time.time() - last_trade_ts >= INTRADAY_T["min_trade_interval_sec"]:
                        msg = "日内T信号: {} (评分{})".format(action, result.get("score"))
                        print("\n🔔 {}".format(msg))
                        _log_alert(msg)
                        prev_t = new_t
                        prev_action = action
                        last_trade_ts = time.time()
                    else:
                        print("\n⏳ 信号 {} (冷却中，维持 {:.0%} T)".format(action, prev_t or 0))
                print("\n下次刷新: {}秒后".format(interval))
                time.sleep(interval)
                print("\n" + "=" * 60 + "\n")
            except KeyboardInterrupt:
                print("\n已停止日内T监控")
                break
            except Exception as e:
                print("错误: {}".format(e), file=sys.stderr)
                time.sleep(interval)
    else:
        run_once(prev_t=prev_t, as_json=args.json)


if __name__ == "__main__":
    main()
