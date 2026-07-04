#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import subprocess
import sys
import time

INJECT_PATH = "/Users/JIN_1/Desktop/jinghe-tracker/_inject.js"
NOTEBOOK_URL = (
    "https://supermind.10jqka.com.cn/notebook/user/615774912/lab/"
    "workspaces/auto-4/tree/Untitled.ipynb"
)

CELL2 = """# Step 2: 回测
btest = research_strategy(
    SOURCE_CODE,
    start_date='20250301',
    end_date='20260703',
    capital_base=200000,
    frequency='DAILY',
    stock_market='STOCK',
    benchmark='000688.SH',
)

print('=== 持仓曲线 ===')
display(btest['analyser']['portfolio'])
print('=== 交易明细 ===')
display(btest['analyser']['trades'])
"""


def build_js(code, cell_index=1):
    return (
        "(function(){\n"
        "  var CODE=" + json.dumps(code, ensure_ascii=False) + ";\n"
        "  var cells=document.querySelectorAll('.jp-CodeCell');\n"
        "  var cell=cells[" + str(cell_index) + "]||cells[cells.length-1];\n"
        "  if(!cell) return 'NO_CELL';\n"
        "  cell.click();\n"
        "  var ed=cell.querySelector('.cm-editor');\n"
        "  if(!(ed&&ed.cmView&&ed.cmView.view)) return 'NO_EDITOR';\n"
        "  var v=ed.cmView.view, len=v.state.doc.length;\n"
        "  v.dispatch({changes:{from:0,to:len,insert:CODE}});\n"
        "  var app=(window.jupyterlab&&window.jupyterlab.application)||null;\n"
        "  if(!app||!app.commands) return 'NO_APP';\n"
        "  app.commands.execute('notebook:run-cell');\n"
        "  return 'RUN_TRIGGERED';\n"
        "})()\n"
    )


def chrome_js(js):
    with open(INJECT_PATH, "w", encoding="utf-8") as f:
        f.write(js)
    script = (
        "tell application \"Google Chrome\"\n"
        "  activate\n"
        "  set targetTab to missing value\n"
        "  repeat with w in windows\n"
        "    set ti to 1\n"
        "    repeat with t in tabs of w\n"
        "      if URL of t contains \"Untitled.ipynb\" then\n"
        "        set targetTab to t\n"
        "        set active tab index of w to ti\n"
        "        exit repeat\n"
        "      end if\n"
        "      set ti to ti + 1\n"
        "    end repeat\n"
        "    if targetTab is not missing value then exit repeat\n"
        "  end repeat\n"
        "  if targetTab is missing value then return \"NO_TAB\"\n"
        '  set jsContent to do shell script "cat " & quoted form of "'
        + INJECT_PATH
        + "\"\n"
        "  return execute targetTab javascript jsContent\n"
        "end tell"
    )
    p = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return (p.stdout or "").strip()


def read_outputs():
    js = (
        "(()=>{const outs=[...document.querySelectorAll("
        "'.jp-OutputArea-output pre, .jp-OutputArea-output')]"
        ".map(e=>(e.textContent||'').trim()).filter(Boolean);"
        "return JSON.stringify(outs.slice(-12));})()"
    )
    return chrome_js(js)


def main():
    print("Step 2: 注入回测代码并运行 …")
    result = chrome_js(build_js(CELL2, cell_index=1))
    print("RUN:", result)
    if result == "NO_TAB":
        print("未找到 Untitled.ipynb 标签页，请先完成 Step 1")
        return 1

    print("回测运行中，等待 30 秒 …")
    time.sleep(30)
    outputs = read_outputs()
    print("OUTPUT:", outputs[:2000] if len(outputs) > 2000 else outputs)

    if "持仓曲线" in outputs or "portfolio" in outputs.lower():
        print("\n✅ Step 2 回测已触发并完成输出")
        return 0
    if result == "RUN_TRIGGERED":
        print("\n⚠ 回测已触发，请在 Chrome 中查看 Notebook 输出")
        return 0
    print("\n❌ Step 2 未完成:", result)
    return 1


if __name__ == "__main__":
    sys.exit(main())
