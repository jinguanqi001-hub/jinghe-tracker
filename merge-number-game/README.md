# 数字三合

三合一数字合成微信小游戏：在 5×5 棋盘上放置数字，**三个相同数字相邻即合成更大数字**，追求高分与更大数字。

## 玩法

1. 点击空格放置「下一个」数字
2. 横/竖相邻的 ≥3 个相同数字合并为 1 个，数值 +1
3. 合并可触发连锁反应
4. 棋盘满格则游戏结束

详细设计见 [GAME_DESIGN.md](./GAME_DESIGN.md)。

## 目录结构

```
merge-number-game/
├── game.js              # 入口
├── game.json
├── project.config.json
├── GAME_DESIGN.md       # 完整策划文档
└── js/
    ├── main.js          # 主循环
    ├── config.js        # 配置与数值
    ├── board.js         # 棋盘
    ├── merge.js         # 三合一算法
    ├── renderer.js      # Canvas 渲染
    ├── input.js         # 触摸输入
    └── storage.js       # 最高分存档
```

## 运行方式

### 微信开发者工具（推荐）

1. 下载 [微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)
2. 选择「小游戏」→ 导入项目 → 目录选 `merge-number-game`
3. AppID 可用测试号，编译后即可试玩

### 浏览器预览（开发调试）

微信小游戏使用 ES Module，浏览器需通过本地服务器打开。可用微信开发者工具的「预览」功能，或将 `js/` 改为打包后的单文件后 HTML 引入。

## 后续扩展

- 合并动画与音效
- 好友排行榜（开放数据域）
- 激励视频复活
- 每日挑战固定种子

## 许可

MIT
