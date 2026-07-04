#!/bin/bash
# 单格部署：策略 + 回测 + 对比买入持有
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$DIR/paste_to_supermind.py" combined >/dev/null

osascript <<'APPLESCRIPT'
tell application "Google Chrome"
  activate
  set found to false
  repeat with w in windows
    set ti to 1
    repeat with t in tabs of w
      if URL of t contains "615774912/lab" then
        set found to true
        set active tab index of w to ti
        exit repeat
      end if
      set ti to ti + 1
    end repeat
    if found then exit repeat
  end repeat
  if not found then
    make new tab at end of tabs of front window with properties {URL:"https://supermind.10jqka.com.cn/notebook/user/615774912/lab/workspaces/auto-T/tree/Untitled.ipynb"}
    delay 10
  end if
end tell
delay 1
tell application "Google Chrome"
  repeat with t in tabs of front window
    if URL of t contains "Untitled.ipynb" or URL of t contains "615774912/lab" then
      set js to "(function(){var cells=document.querySelectorAll('.jp-CodeCell');var c=cells[cells.length-1]||cells[0];if(!c)return 'NO';c.scrollIntoView({block:'center'});c.click();return 'OK';})()"
      execute t javascript js
      exit repeat
    end if
  end repeat
end tell
delay 0.8
tell application "System Events"
  tell process "Google Chrome"
    set frontmost to true
    key code 53
    delay 0.2
    keystroke "b"
    delay 0.3
    key code 36
    delay 0.4
    keystroke "v" using command down
    delay 1.0
    keystroke return using {shift down}
  end tell
end tell
return "combined_run"
APPLESCRIPT

echo "已粘贴并运行合并回测格，请查看 Chrome 输出中的「收益对比」"
