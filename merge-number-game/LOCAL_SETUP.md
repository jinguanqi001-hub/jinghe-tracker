# 本地部署指南（Mac）

把云端项目同步到你的 Mac，并在微信开发者工具中运行。

## 最快方式：一条命令

在 Mac **终端** 粘贴运行：

```bash
curl -fsSL https://raw.githubusercontent.com/jinguanqi001-hub/jinghe-tracker/cursor/wechat-merge-number-game-be47/merge-number-game/scripts/sync-to-local-mac.sh | bash
```

完成后项目会在：

```
~/Projects/merge-number-game
```

Finder 会自动打开该文件夹。

---

## 方式二：Git 克隆（适合后续继续开发）

```bash
# 1. 克隆仓库
cd ~/Projects
git clone -b cursor/wechat-merge-number-game-be47 https://github.com/jinguanqi001-hub/jinghe-tracker.git

# 2. 进入小游戏目录
cd jinghe-tracker/merge-number-game
```

以后云端有更新时，在仓库目录执行：

```bash
cd ~/Projects/jinghe-tracker
git pull origin cursor/wechat-merge-number-game-be47
```

---

## 方式三：直接下载 ZIP（不用 Git）

1. 打开：  
   https://github.com/jinguanqi001-hub/jinghe-tracker/archive/cursor/wechat-merge-number-game-be47.zip
2. 解压 ZIP
3. 进入 `jinghe-tracker-cursor-wechat-merge-number-game-be47/merge-number-game`
4. 把这个 `merge-number-game` 文件夹挪到 `~/Projects/merge-number-game`

---

## 导入微信开发者工具

1. 打开 **微信开发者工具**
2. 点 **「+」** → 选 **「小游戏」**
3. **目录**：选 `~/Projects/merge-number-game`
4. **AppID**：选 **「测试号」**
5. 点 **「导入」** → **「编译」**

### 命令行导入（可选）

先在工具里开启：**设置 → 安全设置 → 服务端口**

```bash
/Applications/wechatwebdevtools.app/Contents/MacOS/cli open --project ~/Projects/merge-number-game
```

---

## 本地目录结构

```
~/Projects/
├── jinghe-tracker/          # 完整 Git 仓库（方式二）
│   └── merge-number-game/   # 小游戏源码
└── merge-number-game/       # 独立副本（方式一脚本生成）
    ├── game.js
    ├── game.json
    ├── project.config.json
    └── js/
```

---

## 常见问题

**Q: 云端改了代码，本地怎么更新？**  
A: 重新运行上面的 `sync-to-local-mac.sh`，或在 `jinghe-tracker` 目录 `git pull`。

**Q: 想用 Cursor 本地编辑？**  
A: 在 Mac 打开 Cursor → File → Open Folder → 选 `~/Projects/merge-number-game` 或整个 `jinghe-tracker`。

**Q: 编译报错？**  
A: 详情 → 本地设置 → 勾选「增强编译」「将 JS 编译成 ES5」，再点编译。
