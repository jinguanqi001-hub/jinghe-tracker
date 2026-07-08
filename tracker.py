#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
晶合集成 (688249) 量化跟踪程序

用法:
  python3 tracker.py                    # 同花顺数据 + 双源对比
  python3 tracker.py --watch 300        # 每300秒刷新
  python3 tracker.py --iwencai          # 附加问财查询
  python3 tracker.py --open-iwencai     # 浏览器打开问财
  python3 tracker.py --source ths       # 指定主数据源
  python3 tracker.py --no-compare       # 关闭双源对比
  python3 tracker.py --intraday-t      # 日内T (华虹分钟基准)
  python3 tracker.py --intraday-t --watch 60
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

from config import ALERT_LOG, STOCK_NAME
from data_fetcher import (
    fetch_daily_klines,
    fetch_realtime,
    get_source_label,
    load_cache,
    open_ths_page,
    save_cache,
)
from indicators import compute_all
from iwencai_client import open_iwencai, query as iwencai_query
from report import render_report
from signals import evaluate
from snapshot import append_snapshot
from source_compare import run_full_compare
from t_signals import evaluate_t_trading


def evaluate_intraday_t_trading():
    """日内T — 华虹分钟 tick 基准"""
    try:
        from ths_fetcher import fetch_benchmark_intraday, fetch_intraday
        from intraday_t_logic import evaluate_intraday_t
        hh = fetch_benchmark_intraday()
        jh = fetch_intraday()
        return evaluate_intraday_t(hh, jh)
    except Exception as e:
        return {"error": str(e), "mode": "intraday"}


def log_alert(message):
    os.makedirs(os.path.dirname(ALERT_LOG) or ".", exist_ok=True)
    line = "[{}] {}\n".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message)
    with open(ALERT_LOG, "a", encoding="utf-8") as f:
        f.write(line)


def run_once(offline=False, as_json=False, source=None, compare=True, iwencai=False, iwencai_preset="fundamental", snapshot=True, t_trading=True, intraday_t=False):
    klines = None
    realtime = None
    src_label = get_source_label(source)
    compare_result = None
    iwencai_result = None

    if not offline:
        try:
            klines = fetch_daily_klines(source=source)
            save_cache(klines, source=source)
            try:
                realtime = fetch_realtime(source=source)
            except Exception:
                realtime = {}
            if compare:
                try:
                    compare_result = run_full_compare()
                except Exception as e:
                    compare_result = {"error": str(e)}
            if iwencai:
                iwencai_result = iwencai_query(preset=iwencai_preset)
        except Exception as e:
            cached = load_cache(source=source)
            if cached:
                klines = cached["klines"]
                realtime = {}
                if not as_json:
                    print("⚠ 网络异常，使用缓存: {}".format(e), file=sys.stderr)
            else:
                raise

    if klines is None:
        cached = load_cache(source=source)
        if not cached:
            raise RuntimeError("无网络且无本地缓存，请先在线运行一次")
        klines = cached["klines"]
        realtime = realtime or {}

    if not klines:
        raise RuntimeError("K线数据为空")

    if not realtime:
        last = klines[-1]
        realtime = {
            "price": last["close"],
            "open": last["open"],
            "high": last["high"],
            "low": last["low"],
            "change_pct": last["change_pct"],
            "turnover_pct": last["turnover_pct"],
            "timestamp": last["date"],
        }

    indicators = compute_all(klines)
    evaluation = evaluate(klines, indicators, realtime)
    t_result = None
    if intraday_t and not offline:
        t_result = evaluate_intraday_t_trading()
    elif t_trading and not offline:
        t_result = evaluate_t_trading(klines, realtime)

    for s in evaluation["signals"]:
        if s["level"] in ("SELL", "WARN"):
            log_alert("[{}] {} — {}".format(s["level"], s["message"], s["action"]))

    if compare_result and not compare_result.get("error"):
        rt = compare_result.get("realtime") or {}
        for a in rt.get("alerts") or []:
            if a.get("level") == "WARN":
                log_alert("[双源] {}".format(a.get("message")))

    if snapshot and not offline:
        try:
            path = append_snapshot(realtime, indicators, evaluation, compare_result, source=src_label)
            if as_json:
                evaluation["_snapshot"] = path
        except Exception:
            pass

    if as_json:
        out = {
            "source": src_label,
            "realtime": realtime,
            "latest_bar": indicators["latest"],
            "indicators": {
                "ma5": indicators["ma5"],
                "ma10": indicators["ma10"],
                "ma20": indicators["ma20"],
                "rsi": indicators["rsi"],
                "deviation_ma20": indicators["deviation_ma20"],
                "macd": indicators["macd"],
            },
            "evaluation": evaluation,
            "compare": compare_result,
            "iwencai": iwencai_result,
            "t_trading": t_result,
        }
        print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
    else:
        print(render_report(
            STOCK_NAME, realtime, indicators, evaluation, src_label,
            compare_result=compare_result if not compare_result or not compare_result.get("error") else None,
            iwencai_result=iwencai_result,
            t_result=t_result,
        ))
        if compare_result and compare_result.get("error"):
            print("\n⚠ 双源对比失败: {}".format(compare_result["error"]))

    return evaluation


def main():
    parser = argparse.ArgumentParser(description="晶合集成 688249 量化跟踪")
    parser.add_argument("--watch", type=int, metavar="SEC", help="定时刷新间隔(秒)")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--offline", action="store_true", help="仅使用本地缓存")
    parser.add_argument(
        "--source",
        choices=["ths", "eastmoney", "ifind", "auto"],
        help="主数据源",
    )
    parser.add_argument("--open-ths", action="store_true", help="浏览器打开同花顺个股页")
    parser.add_argument("--no-compare", action="store_true", help="关闭双源对比")
    parser.add_argument("--iwencai", action="store_true", help="附加问财查询")
    parser.add_argument(
        "--iwencai-preset",
        choices=["fundamental", "flow", "industry", "risk"],
        default="fundamental",
        help="问财预设问句",
    )
    parser.add_argument("--open-iwencai", action="store_true", help="浏览器打开问财")
    parser.add_argument("--no-snapshot", action="store_true", help="不写入每日快照 CSV")
    parser.add_argument("--no-t", action="store_true", help="不显示华虹做T建议")
    parser.add_argument("--intraday-t", action="store_true", help="日内T模式(华虹分钟基准，替代日线T)")
    args = parser.parse_args()

    if args.open_ths:
        url = open_ths_page()
        print("已打开同花顺: {}".format(url))

    if args.open_iwencai:
        url = open_iwencai(preset=args.iwencai_preset)
        print("已打开问财: {}".format(url))
        if not args.watch and not args.json and not args.iwencai:
            return

    compare = not args.no_compare
    snapshot = not args.no_snapshot
    t_trading = not args.no_t and not args.intraday_t
    intraday_t = args.intraday_t

    if args.watch:
        interval = max(60, args.watch)
        print("监控模式: 每 {} 秒刷新 (Ctrl+C 退出)\n".format(interval))
        prev_verdict = None
        while True:
            try:
                ev = run_once(
                    offline=args.offline,
                    as_json=False,
                    source=args.source,
                    compare=compare,
                    iwencai=args.iwencai,
                    iwencai_preset=args.iwencai_preset,
                    snapshot=snapshot,
                    t_trading=t_trading,
                    intraday_t=intraday_t,
                )
                if prev_verdict and ev["verdict"] != prev_verdict:
                    msg = "研判变化: {} → {}".format(prev_verdict, ev["verdict"])
                    print("\n🔔 {}".format(msg))
                    log_alert(msg)
                prev_verdict = ev["verdict"]
                print("\n下次刷新: {}秒后".format(interval))
                time.sleep(interval)
                print("\n" + "=" * 60 + "\n")
            except KeyboardInterrupt:
                print("\n已停止监控")
                break
            except Exception as e:
                print("错误: {}".format(e), file=sys.stderr)
                time.sleep(interval)
    else:
        run_once(
            offline=args.offline,
            as_json=args.json,
            source=args.source,
            compare=compare,
            iwencai=args.iwencai,
            iwencai_preset=args.iwencai_preset,
            snapshot=snapshot,
            t_trading=t_trading,
            intraday_t=intraday_t,
        )


if __name__ == "__main__":
    main()
