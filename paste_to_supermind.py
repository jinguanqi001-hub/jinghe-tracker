#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 SuperMind 策略代码复制到剪贴板（等价于上传后的 Step 1 代码格）"""
import re
import subprocess
import sys

PY_FILE = "/Users/JIN_1/Desktop/jinghe-tracker/supermind_jinghe.py"
URL = "https://quant.10jqka.com.cn/platform/html/study-research.html"


def load_cell1():
    with open(PY_FILE, "r", encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"(SOURCE_CODE = r'''\n.*?\n''')", text, re.DOTALL)
    if not m:
        raise SystemExit("找不到 SOURCE_CODE")
    return (
        m.group(1)
        + "\n\nprint('✓ 策略代码已加载，共', len(SOURCE_CODE), '字符')\n"
        + "print('✓ Step 1 就绪 — 请运行下一个单元格开始回测 (Step 2)')\n"
    )


BACKTEST_START = '20250201'
BACKTEST_END = '20260703'


def load_cell2():
    return """# Step 2: 回测 + 量价策略 vs 买入持有
btest = research_strategy(
    SOURCE_CODE,
    start_date='""" + BACKTEST_START + """',
    end_date='""" + BACKTEST_END + """',
    capital_base=200000,
    frequency='DAILY',
    stock_market='STOCK',
    benchmark='000688.SH',
)

pf = btest['analyser']['portfolio']
trades = btest['analyser']['trades']
final_tv = float(pf['total_value'].iloc[-1])
init_tv = float(pf['total_value'].iloc[0])
strat_ret = (final_tv / init_tv - 1) * 100

px = get_price('688249.SH', '""" + BACKTEST_START + """', '""" + BACKTEST_END + """', '1d', ['close'], True, 'pre', 0, False)
if isinstance(px, dict):
    px = px['688249.SH']
start_px = float(px['close'].iloc[0])
end_px = float(px['close'].iloc[-1])
bh_ret = (end_px / start_px - 1) * 100
bh_tv = init_tv * (end_px / start_px)

n_trades = len(trades) if trades is not None else 0
pos_pf = pf[pf['market_value'] > 0]

print('=== 回测摘要 (v7.2 领先股仅建仓) ===')
print('区间: """ + BACKTEST_START + """ ~ """ + BACKTEST_END + """')
print('领先股: 688347华虹 / 688361中科飞测 / 688082盛美上海')
print('688249 股价: {:.2f} -> {:.2f}  涨幅 {:.2f}%'.format(start_px, end_px, bh_ret))
print('买入持有估算: {:.2f}%  (期末 {:.0f})'.format(bh_ret, bh_tv))
print('策略收益率:   {:.2f}%  (期末 {:.0f})'.format(strat_ret, final_tv))
print('超额收益:     {:.2f}%'.format(strat_ret - bh_ret))
print('成交笔数:     {}'.format(n_trades))
print('信号说明: 晶合量价卖出 + 领先股(华虹/设备)仅建仓')

print('=== 持仓曲线 ===')
display(pf)
print('=== 交易明细 ===')
display(trades)
"""


def load_combined():
    with open(PY_FILE, "r", encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"SOURCE_CODE = r'''(.*?)'''", text, re.DOTALL)
    if not m:
        raise SystemExit("找不到 SOURCE_CODE")
    backtest = load_cell2().split("\n", 1)[1]
    return (
        "SOURCE_CODE = r'''" + m.group(1) + "'''\n\n"
        "print('✓ 策略已加载', len(SOURCE_CODE), '字符')\n\n"
        + backtest
    )


def to_clipboard(text):
    p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
    p.communicate(text.encode("utf-8"))


def load_intraday_cell():
    return """# Step 2B: 日内T 分钟回测 (v10)
from supermind_jinghe import INTRADAY_SOURCE_CODE

btest = research_strategy(
    INTRADAY_SOURCE_CODE,
    start_date='20250601',
    end_date='20260703',
    capital_base=200000,
    frequency='MINUTE',
    stock_market='STOCK',
    benchmark='000688.SH',
)

pf = btest['analyser']['portfolio']
trades = btest['analyser']['trades']
print('=== 日内T 分钟回测 ===')
display(pf)
display(trades)
"""


def main():
    cell = sys.argv[1] if len(sys.argv) > 1 else "1"
    if cell in ("all", "3", "combined"):
        content = load_combined()
        label = "合并格(策略+回测)"
    elif cell in ("intraday", "minute", "t"):
        content = load_intraday_cell()
        label = "日内T分钟回测"
    elif cell == "2":
        content = load_cell2()
        label = "第 2 格"
    else:
        content = load_cell1()
        label = "第 1 格"
    to_clipboard(content)
    print("=" * 50)
    print("✓ {} 已复制到剪贴板 ({} 字符)".format(label, len(content)))
    print("请在 SuperMind Notebook 新建空白格 → 粘贴 → Shift+Enter")
    if cell == "1":
        print("然后: python3 paste_to_supermind.py 2")
    elif cell in ("all", "3", "combined"):
        print("（单格即可完成回测与收益对比）")
    print("=" * 50)


if __name__ == "__main__":
    main()
