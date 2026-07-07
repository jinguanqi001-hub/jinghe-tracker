#!/bin/bash
# 在 Mac 上一键下载并安装「微信开发者工具」（稳定版）
# 用法：bash install-wechat-devtools-mac.sh

set -euo pipefail

VERSION="2.01.2510290"
DOWNLOAD_DIR="${HOME}/Downloads"
FILENAME="wechat_devtools_${VERSION}_darwin"

echo "========================================"
echo "  微信开发者工具 Mac 安装助手"
echo "  稳定版: ${VERSION}"
echo "========================================"
echo ""

# 检测芯片架构
ARCH=$(uname -m)
if [[ "$ARCH" == "arm64" ]]; then
  CHIP="Apple Silicon (M 系列)"
  URL="https://servicewechat.com/wxa-dev-logic/download_redirect?type=darwin_arm64&from=mpwiki&download_version=2012510290&version_type=1"
  OUT="${DOWNLOAD_DIR}/${FILENAME}_arm64.dmg"
elif [[ "$ARCH" == "x86_64" ]]; then
  CHIP="Intel"
  URL="https://servicewechat.com/wxa-dev-logic/download_redirect?type=darwin_x64&from=mpwiki&download_version=2012510290&version_type=1"
  OUT="${DOWNLOAD_DIR}/${FILENAME}_x64.dmg"
else
  echo "❌ 不支持的架构: $ARCH"
  exit 1
fi

echo "检测到: ${CHIP}"
echo "下载目录: ${OUT}"
echo ""

# 方式一：优先尝试 Homebrew（已安装则最快）
if command -v brew &>/dev/null; then
  echo "检测到 Homebrew，推荐使用 brew 安装..."
  read -r -p "是否用 Homebrew 安装？(Y/n) " USE_BREW
  USE_BREW=${USE_BREW:-Y}
  if [[ "$USE_BREW" =~ ^[Yy]$ ]]; then
    brew install --cask wechatwebdevtools
    echo ""
    echo "✅ 安装完成！在启动台搜索「微信开发者工具」打开即可。"
    echo ""
    echo "导入小游戏项目："
    echo "  1. 打开微信开发者工具"
    echo "  2. 选择「小游戏」"
    echo "  3. 导入本仓库的 merge-number-game 目录"
    exit 0
  fi
fi

# 方式二：直接下载 DMG
echo "正在从微信官方服务器下载..."
if command -v curl &>/dev/null; then
  curl -L --progress-bar -o "$OUT" "$URL"
elif command -v wget &>/dev/null; then
  wget -O "$OUT" "$URL"
else
  echo "❌ 需要 curl 或 wget，请先安装 Xcode Command Line Tools："
  echo "   xcode-select --install"
  exit 1
fi

if [[ ! -f "$OUT" ]] || [[ ! -s "$OUT" ]]; then
  echo "❌ 下载失败，请手动打开官方页面："
  echo "   https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html"
  exit 1
fi

echo ""
echo "✅ 下载完成: $OUT"
echo "正在打开安装包..."
open "$OUT"

echo ""
echo "----------------------------------------"
echo "接下来请按图形界面操作："
echo "  1. 在弹出的窗口中把「微信开发者工具」拖到「应用程序」"
echo "  2. 首次打开若提示「无法验证开发者」，请到："
echo "     系统设置 → 隐私与安全性 → 仍要打开"
echo "  3. 用微信扫码登录"
echo "  4. 新建项目 → 选择「小游戏」→ 导入 merge-number-game 目录"
echo "----------------------------------------"
