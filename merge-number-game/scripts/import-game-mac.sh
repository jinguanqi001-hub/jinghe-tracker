#!/bin/bash
# 一键下载并导入「数字三合」到微信开发者工具（Mac）
# 用法：复制下面整段到 Mac 终端运行
#
# curl -fsSL https://raw.githubusercontent.com/jinguanqi001-hub/jinghe-tracker/cursor/wechat-merge-number-game-be47/merge-number-game/scripts/import-game-mac.sh | bash

set -euo pipefail

PROJECT_DIR="${HOME}/Downloads/merge-number-game"
REPO_URL="https://github.com/jinguanqi001-hub/jinghe-tracker.git"
BRANCH="cursor/wechat-merge-number-game-be47"
CLI_PATHS=(
  "/Applications/wechatwebdevtools.app/Contents/MacOS/cli"
  "/Applications/微信开发者工具.app/Contents/MacOS/cli"
)

echo ""
echo "=========================================="
echo "  数字三合 · 一键导入微信开发者工具"
echo "=========================================="
echo ""

# 1. 下载项目
if [[ -f "${PROJECT_DIR}/game.js" && -f "${PROJECT_DIR}/project.config.json" ]]; then
  echo "✓ 项目已存在: ${PROJECT_DIR}"
else
  echo "→ 正在下载项目到 ${PROJECT_DIR} ..."
  TMP=$(mktemp -d)
  git clone --depth 1 --branch "${BRANCH}" "${REPO_URL}" "${TMP}/repo"
  rm -rf "${PROJECT_DIR}"
  cp -R "${TMP}/repo/merge-number-game" "${PROJECT_DIR}"
  rm -rf "${TMP}"
  echo "✓ 下载完成"
fi

# 2. 查找微信开发者工具 CLI
CLI=""
for p in "${CLI_PATHS[@]}"; do
  if [[ -x "$p" ]]; then
    CLI="$p"
    break
  fi
done

if [[ -z "$CLI" ]]; then
  echo ""
  echo "⚠ 未找到微信开发者工具 CLI，将用 Finder 打开项目文件夹。"
  echo "  请手动在微信开发者工具中："
  echo "    1. 点左上角「+」"
  echo "    2. 选择「小游戏」"
  echo "    3. 目录选: ${PROJECT_DIR}"
  echo "    4. AppID 选「测试号」"
  echo ""
  open "${PROJECT_DIR}"
  exit 0
fi

echo "✓ 找到开发者工具: ${CLI}"
echo ""
echo "⚠ 首次使用 CLI 导入前，请确认已开启服务端口："
echo "   微信开发者工具 → 设置 → 安全设置 → 开启服务端口"
echo ""
read -r -p "已开启服务端口？按回车继续，或 Ctrl+C 取消..." _

echo ""
echo "→ 正在打开并导入项目..."
"${CLI}" open --project "${PROJECT_DIR}"

echo ""
echo "=========================================="
echo "  导入完成！"
echo "  项目路径: ${PROJECT_DIR}"
echo ""
echo "  若模拟器没出现游戏："
echo "    1. 点顶部「编译」"
echo "    2. 详情 → 本地设置 → 勾选「增强编译」"
echo "=========================================="
echo ""
