# SuperMind 下一步操作指南（晶合集成 688249）

你已登录 SuperMind，按下面 **5 步** 走，不要跳过回测直接实盘。

---

## Step 0：确认环境

| 检查项 | 要求 |
|--------|------|
| 研究环境 | 选 **Python 3.8**（JupyterLab） |
| 客户端 | SuperMind PC 端已登录（仿真/实盘需要） |
| 权限 | 已开通 **科创板 (688)** 交易权限 |
| 本地策略 | `~/Desktop/jinghe-tracker/supermind_jinghe.py` |

---

## Step 1：打开研究环境

1. SuperMind 客户端 → 点击 **「研究一下」** 或进入 **研究环境**
2. 新建 Notebook（`.ipynb`）
3. 打开本地文件 `supermind_jinghe.py`，复制 **`SOURCE_CODE`** 整段到 Notebook

---

## Step 2：先回测（必做）

在新单元格运行：

```python
btest = research_strategy(
    SOURCE_CODE,
    start_date='20250301',
    end_date='20260703',
    capital_base=200000,
    frequency='DAILY',
    stock_market='STOCK',
    benchmark='000688.SH',
)

# 看结果
btest['analyser']['portfolio']   # 持仓曲线
btest['analyser']['trades']      # 每笔买卖
```

**重点看：**

- 总收益率、最大回撤
- 3–6 月上涨段是否过早卖飞
- 7 月高位是否触发减仓

回测不满意 → 改 `supermind_jinghe.py` 里价位/RSI 参数，再跑。

---

## Step 3：与本地 tracker 对照

终端运行本地监控（Mac 可做）：

```bash
cd ~/Desktop/jinghe-tracker && python3 tracker.py
```

对比 SuperMind 回测信号日 与 tracker 的 **评分/研判** 是否一致。  
若不一致，以 **回测可验证的规则** 为准调整策略。

---

## Step 4：仿真交易（实盘前最后一关）

1. 客户端首页 → 获取 **仿真资金账号**
2. 在 Notebook 运行：

```python
from tick_trade_api import TradeAPI, LimitPolicy

trade_api = TradeAPI('仿真账号', order_policy=LimitPolicy)

rtrade = research_trade(
    '晶合688249策略',
    SOURCE_CODE,
    capital_base=200000,
    frequency='DAILY',
    trade_api=trade_api,
    signal_mode=True,    # 新手务必 True
    recover_dt='today',
)
```

3. 选中单元格 → 点 **▶ 运行**
4. 观察 3–5 个交易日：委托、成交、持仓是否正常

**注意：**

- 策略请在 **9:00 前** 启动
- **22:05–22:15** 清算时段不下单
- 不要在策略运行期间 **手动买卖 688249**（会被策略干扰）

---

## Step 5：真实实盘（可选，仿真稳定后再做）

1. 联系 SuperMind 开通 **真实资金账号** 接入（社区/邮件 SuperMind@myhexin.com）
2. 将 `TradeAPI('仿真账号')` 换成 **真实资金账号**
3. 先用 **小仓位**（如 2–3 万元）跑 1–2 周
4. 688249 波动大（±20%），建议 `MAX_POSITION_PCT = 0.2` 或更低

---

## 策略 v7 — 量价 + 领先股联动

**领先指标（走势同步、historically 更早启动）**

| 代码 | 名称 | 权重 |
|------|------|------|
| 688347 | 华虹公司 | 1.2 |
| 688361 | 中科飞测 | 1.0 |
| 688082 | 盛美上海 | 1.0 |

| 逻辑 | 说明 |
|------|------|
| 晶合自身 | v6 量价买卖（58/52 突破、放量上影、破均线等） |
| **领先建仓** | 华虹/设备出现放量买信号 → 晶合加分；领先强时晶合尚未启动也可建仓 |
| **领先减仓** | 领先股放量出货/破均线 → 晶合提前降仓 |

```bash
python3 paste_to_supermind.py combined
```

回测区间：`20250201` ~ `20260703`（2025年2月至今）

---

## 常见问题

**Q：研究环境找不到 `research_strategy`？**  
→ 重启研究环境；确认在 SuperMind 内运行，不是本地 Python。

**Q：回测有信号，仿真没下单？**  
→ 检查 `TradeAPI` 账号、9 点前是否启动、`signal_mode` 与持仓权限。

**Q：能否用问财选股？**  
→ 本策略单票 688249 不需要；若扩展板块轮动，可用 `get_iwencai('晶圆代工', 'pool')`。

**Q：Mac 能否仿真？**  
→ 研究环境可在网页；**TradeAPI 仿真/实盘需 Windows SuperMind 客户端** 并保持登录。

---

## 推荐时间线

```
今天     → Step 1–2 回测
本周     → Step 3 对照 tracker + 调参
下周     → Step 4 仿真 3–5 天
H股上市后 → 再评估是否 Step 5 小仓实盘
```

---

## 官方资源

- 实盘教程：https://quant.10jqka.com.cn/view/help/14
- 1 分钟实盘模板：https://quant.10jqka.com.cn/view/article/2358
- 社区提问：SuperMind 官方社区
