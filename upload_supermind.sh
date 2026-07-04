#!/bin/bash
# 一键辅助上传 SuperMind Notebook（需已登录浏览器）

FILE="/Users/JIN_1/Desktop/jinghe688249_supermind.ipynb"
URL="https://quant.10jqka.com.cn/platform/html/study-research.html"

echo "正在打开 SuperMind 研究环境..."
open "$URL"

sleep 1
echo "正在定位 Notebook 文件..."
open -R "$FILE"

osascript <<'EOF'
display dialog "你已登录 SuperMind，请按下面 3 步上传：

1️⃣ 浏览器左侧点「我的研究」
2️⃣ 点「上传」按钮（或 ↑ 图标）
3️⃣ 选桌面上的 jinghe688249_supermind.ipynb

上传后：
• 点开 Notebook
• 内核选 Python 3.8
• 运行第 1 格

若找不到上传按钮 → 点「新建」→「Notebook」→ Cmd+V 粘贴（代码已在剪贴板）" buttons {"知道了"} default button 1 with title "SuperMind 上传指引" with icon note
EOF

echo "完成。文件路径: $FILE"
