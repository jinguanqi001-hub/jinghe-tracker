#!/bin/bash
# ============================================================
#  数字三合 · Mac 本地一键安装脚本
#  在 Cursor 终端粘贴运行：
#
#  curl -fsSL https://raw.githubusercontent.com/jinguanqi001-hub/jinghe-tracker/cursor/wechat-merge-number-game-be47/merge-number-game/scripts/setup-local-mac.sh | bash
# ============================================================

set -euo pipefail

PROJECT_DIR="${HOME}/Projects/merge-number-game"
REPO_URL="https://github.com/jinguanqi001-hub/jinghe-tracker.git"
BRANCH="cursor/wechat-merge-number-game-be47"
CLI="/Applications/wechatwebdevtools.app/Contents/MacOS/cli"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   数字三合 · 本地环境一键安装            ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── 1. 检查 / 安装 Homebrew ──────────────────────────────
if ! command -v brew &>/dev/null; then
  echo "→ [1/4] 安装 Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  # Apple Silicon 路径
  if [[ -f /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  fi
else
  echo "✓ [1/4] Homebrew 已安装"
fi

# ── 2. 检查 / 安装微信开发者工具 ─────────────────────────
if [[ -d "/Applications/wechatwebdevtools.app" ]]; then
  echo "✓ [2/4] 微信开发者工具已安装"
else
  echo "→ [2/4] 安装微信开发者工具（可能需要几分钟）..."
  brew install --cask wechatwebdevtools
  echo "✓ 微信开发者工具安装完成"
fi

# ── 3. 下载项目到本地 ────────────────────────────────────
echo "→ [3/4] 同步项目到 ${PROJECT_DIR} ..."
mkdir -p "${HOME}/Projects"
TMP=$(mktemp -d)
git clone --depth 1 --branch "${BRANCH}" "${REPO_URL}" "${TMP}/repo"
rm -rf "${PROJECT_DIR}"
cp -R "${TMP}/repo/merge-number-game" "${PROJECT_DIR}"
rm -rf "${TMP}"
echo "✓ 项目已同步"

# ── 4. 用 Cursor 打开项目 ────────────────────────────────
echo "→ [4/4] 打开项目..."
if command -v cursor &>/dev/null; then
  cursor "${PROJECT_DIR}" &
  echo "✓ 已在 Cursor 中打开项目"
elif [[ -d "/Applications/Cursor.app" ]]; then
  open -a Cursor "${PROJECT_DIR}"
  echo "✓ 已在 Cursor 中打开项目"
else
  open "${PROJECT_DIR}"
  echo "✓ 已在 Finder 中打开项目（未检测到 Cursor 命令）"
fi

# ── 尝试用 CLI 导入微信开发者工具 ───────────────────────
echo ""
if [[ -x "${CLI}" ]]; then
  echo "→ 尝试自动导入微信开发者工具..."
  echo "  （若失败，请手动：设置 → 安全设置 → 开启服务端口）"
  "${CLI}" open --project "${PROJECT_DIR}" 2>/dev/null && \
    echo "✓ 已导入微信开发者工具" || \
    echo "⚠ 自动导入失败，请按下方手动步骤操作"
else
  echo "⚠ 未找到 CLI，请手动打开微信开发者工具导入"
fi

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  安装完成！                              ║"
echo "╠══════════════════════════════════════════╣"
echo "║  项目路径:                               ║"
echo "║  ${PROJECT_DIR}"
echo "╠══════════════════════════════════════════╣"
echo "║  若未自动导入，请手动：                  ║"
echo "║  1. 打开微信开发者工具                   ║"
echo "║  2. 点「+」→ 选「小游戏」               ║"
echo "║  3. 目录选上方路径                       ║"
echo "║  4. AppID 选「测试号」→ 编译             ║"
echo "╚══════════════════════════════════════════╝"
echo ""
