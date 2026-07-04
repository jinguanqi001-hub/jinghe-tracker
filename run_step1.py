#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import subprocess
import sys
import time

NB_PATH = "/Users/JIN_1/Desktop/jinghe688249_supermind.ipynb"
INJECT_PATH = "/Users/JIN_1/Desktop/jinghe-tracker/_inject.js"
NOTEBOOK_URL = (
    "https://supermind.10jqka.com.cn/notebook/user/615774912/lab/"
    "workspaces/auto-4/tree/Untitled.ipynb"
)


def load_cell1():
    import re
    with open("/Users/JIN_1/Desktop/jinghe-tracker/supermind_jinghe.py", "r", encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"(SOURCE_CODE = r'''\n.*?\n''')", text, re.DOTALL)
    if not m:
        raise SystemExit("找不到 SOURCE_CODE")
    return (
        m.group(1)
        + "\n\nprint('✓ 策略代码已加载，共', len(SOURCE_CODE), '字符')\n"
        + "print('✓ Step 1 就绪 — 请运行下一个单元格开始回测 (Step 2)')\n"
    )


def build_js(code):
    return (
        "(function(){\n"
        "  var CODE=" + json.dumps(code, ensure_ascii=False) + ";\n"
        "  function inject(){\n"
        "    var cell=document.querySelector('.jp-CodeCell.jp-mod-active')"
        "||document.querySelector('.jp-CodeCell');\n"
        "    if(!cell) return 'NO_CELL';\n"
        "    cell.click();\n"
        "    var ed=cell.querySelector('.cm-editor');\n"
        "    if(ed&&ed.cmView&&ed.cmView.view){\n"
        "      var v=ed.cmView.view, len=v.state.doc.length;\n"
        "      v.dispatch({changes:{from:0,to:len,insert:CODE}});\n"
        "      return 'OK';\n"
        "    }\n"
        "    return 'NO_EDITOR';\n"
        "  }\n"
        "  var st=inject();\n"
        "  if(st!=='OK') return st;\n"
        "  var app=(window.jupyterlab&&window.jupyterlab.application)||null;\n"
        "  if(!app||!app.commands) return 'NO_APP';\n"
        "  app.commands.execute('notebook:run-cell');\n"
        "  return 'RUN_TRIGGERED';\n"
        "})()\n"
)


def _applescript_body(js_action):
    return (
        "tell application \"Google Chrome\"\n"
        "  activate\n"
        "  set targetTab to missing value\n"
        "  repeat with w in windows\n"
        "    set ti to 1\n"
        "    repeat with t in tabs of w\n"
        "      set u to URL of t\n"
        "      if u contains \"Untitled.ipynb\" then\n"
        "        set targetTab to t\n"
        "        set active tab index of w to ti\n"
        "        exit repeat\n"
        "      end if\n"
        "      set ti to ti + 1\n"
        "    end repeat\n"
        "    if targetTab is not missing value then exit repeat\n"
        "  end repeat\n"
        "  if targetTab is missing value then\n"
        "    set targetTab to make new tab at end of tabs of front window "
        "with properties {URL:\"" + NOTEBOOK_URL + "\"}\n"
        "    delay 12\n"
        "  end if\n"
        + js_action
        + "\nend tell"
    )


def chrome_js(js):
    with open(INJECT_PATH, "w", encoding="utf-8") as f:
        f.write(js)
    script = _applescript_body(
        '  set jsContent to do shell script "cat " & quoted form of "'
        + INJECT_PATH
        + "\"\n"
        "  return execute targetTab javascript jsContent\n"
    )
    p = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return (p.stdout or "").strip(), (p.stderr or "").strip()


def read_outputs():
    js = (
        "(()=>{const outs=[...document.querySelectorAll("
        "'.jp-OutputArea-output pre, .jp-OutputArea-output')]"
        ".map(e=>(e.textContent||'').trim()).filter(Boolean);"
        "return JSON.stringify(outs.slice(-8));})()"
    )
    out, err = chrome_js(js)
    return out or err


def scan_notebook():
    js = (
        "(()=>JSON.stringify({url:location.href,"
        "cells:document.querySelectorAll('.jp-CodeCell').length,"
        "hasApp:!!(window.jupyterlab&&window.jupyterlab.application)}))()"
    )
    return chrome_js(js)[0]


def main():
    print("打开 Untitled.ipynb …")
    scan = scan_notebook()
    print("SCAN:", scan)

    code = load_cell1()
    prep_js = (
        "(function(){"
        "var cells=document.querySelectorAll('.jp-CodeCell');"
        "if(!cells.length) return 'NO_CELL';"
        "cells[0].click();"
        "var app=(window.jupyterlab&&window.jupyterlab.application);"
        "if(app&&app.commands){try{app.commands.execute('notebook:insert-cell-below');"
        "setTimeout(function(){},300);}catch(e){}}"
        "return 'prep';})()"
    )
    chrome_js(prep_js)
    time.sleep(1.5)

    result, err = chrome_js(build_js(code))
    if err:
        print("ERR:", err)
    print("RUN:", result)
    time.sleep(8)

    outputs = read_outputs()
    print("OUTPUT:", outputs)

    blob = outputs + result
    if "Step 1 就绪" in blob or "策略代码已加载" in blob:
        print("\n✅ Step 1 已完成")
        return 0
    if result in ("RUN_TRIGGERED", "OK"):
        print("\n⚠ 已触发运行，若输出区有两行 ✓ 则 Step 1 完成")
        return 0
    print("\n❌ 未完成:", result)
    subprocess.run(
        ["python3", "/Users/JIN_1/Desktop/jinghe-tracker/paste_to_supermind.py", "1"]
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
