#!/bin/bash
# 将云端「数字三合」项目同步到 Mac 本地
# 在 Mac 终端粘贴运行：
#   curl -fsSL https://raw.githubusercontent.com/jinguanqi001-hub/jinghe-tracker/cursor/wechat-merge-number-game-be47/merge-number-game/scripts/sync-to-local-mac.sh | bash

set -euo pipefail

REPO="https://github.com/jinguanqi001-hub/jinghe-tracker.git"
BRANCH="cursor/wechat-merge-number-game-be47"
TARGET="${HOME}/Projects/merge-number-game"
FULL_REPO="${HOME}/Projects/jinghe-tracker"

echo ""
echo "=========================================="
echo "  数字三合 · 云端项目同步到本地"
echo "=========================================="
echo ""

# 检查 git
if ! command -v git &>/dev/null; then
  echo "未检测到 git，正在提示安装 Xcode Command Line Tools..."
  xcode-select --install 2>/dev/null || true
  echo "安装完成后重新运行本脚本。"
  exit 1
fi

mkdir -p "${HOME}/Projects"

# 方式：克隆/更新完整仓库，再复制小游戏目录
if [[ -d "${FULL_REPO}/.git" ]]; then
  echo "→ 更新已有仓库..."
  cd "${FULL_REPO}"
  git fetch origin "${BRANCH}"
  git checkout "${BRANCH}" 2>/dev/null || git checkout -b "${BRANCH}" "origin/${BRANCH}"
  git pull origin "${BRANCH}"
else
  echo "→ 正在从 GitHub 克隆..."
  git clone --branch "${BRANCH}" --depth 1 "${REPO}" "${FULL_REPO}"
fi

echo "→ 复制小游戏到独立目录..."
rm -rf "${TARGET}"
cp -R "${FULL_REPO}/merge-number-game" "${TARGET}"

echo ""
echo "✅ 同步完成！"
echo ""
echo "  小游戏目录:  ${TARGET}"
echo "  完整仓库:    ${FULL_REPO}"
echo ""
echo "  下一步（微信开发者工具）："
echo "    1. 打开微信开发者工具"
echo "    2. 点「+」→ 选「小游戏」"
echo "    3. 目录选: ${TARGET}"
echo "    4. AppID 选「测试号」→ 导入 → 编译"
echo ""
echo "  或用命令行一键打开（需先开启服务端口）："
echo "    /Applications/wechatwebdevtools.app/Contents/MacOS/cli open --project ${TARGET}"
echo ""

# 用 Finder 打开项目文件夹
open "${TARGET}"
