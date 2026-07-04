#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$DIR/paste_to_supermind.py" 1 >/dev/null

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
        make new tab at end of tabs of front window with properties {URL:"https://supermind.10jqka.com.cn/notebook/user/615774912/lab"}
        delay 8
    end if
end tell

delay 1.5
tell application "System Events"
    tell process "Google Chrome"
        set frontmost to true
        delay 0.5
        key code 53
        delay 0.2
        keystroke "b"
        delay 0.2
        key code 36
        delay 0.4
        keystroke "v" using command down
        delay 0.6
        keystroke return using {shift down}
    end tell
end tell
return "done"
APPLESCRIPT

echo "自动化已执行。请查看 Chrome 中 Notebook 是否出现 ✓ Step 1 就绪"
