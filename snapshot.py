# -*- coding: utf-8 -*-
"""每日快照记录 — 用于回溯信号与双源价差"""

import csv
import os
from datetime import datetime

from config import DATA_CACHE_DIR, STOCK_CODE

SNAPSHOT_FILE = os.path.join(DATA_CACHE_DIR, "snapshots.csv")

COLUMNS = [
    "datetime",
    "source",
    "price",
    "change_pct",
    "turnover_pct",
    "rsi",
    "score",
    "verdict",
    "ths_price",
    "em_price",
    "price_diff_pct",
    "ah_premium_pct",
]


def append_snapshot(realtime, indicators, evaluation, compare=None, source="ths"):
    os.makedirs(DATA_CACHE_DIR, exist_ok=True)
    write_header = not os.path.isfile(SNAPSHOT_FILE)

    ths_p = em_p = diff_pct = None
    if compare:
        ths_p = (compare.get("realtime") or {}).get("ths", {}).get("price")
        em_p = (compare.get("realtime") or {}).get("eastmoney", {}).get("price")
        diff_pct = (compare.get("realtime") or {}).get("price_diff_pct")

    row = {
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": source,
        "price": realtime.get("price"),
        "change_pct": realtime.get("change_pct"),
        "turnover_pct": realtime.get("turnover_pct"),
        "rsi": indicators.get("rsi"),
        "score": evaluation.get("score"),
        "verdict": evaluation.get("verdict"),
        "ths_price": ths_p,
        "em_price": em_p,
        "price_diff_pct": diff_pct,
        "ah_premium_pct": (evaluation.get("ah_premium") or 0) * 100 if evaluation.get("ah_premium") else None,
    }

    with open(SNAPSHOT_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        if write_header:
            w.writeheader()
        w.writerow(row)
    return SNAPSHOT_FILE


def read_recent(n=10):
    if not os.path.isfile(SNAPSHOT_FILE):
        return []
    with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[-n:]
