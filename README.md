# 晶合集成 (688249) 量化跟踪程序

基于东方财富公开 API，自动拉取行情、计算技术指标、触发我们此前讨论过的量价/事件信号。

## 功能

- 实时行情 + 120 日 K 线
- 技术指标: MA5/10/20、RSI、MACD、BOLL、量比
- 形态识别: 长上影、天量滞涨、放量长阴、67 元三重顶
- 事件监控: H 股上市倒计时、A/H 溢价
- 关键价位距离: 58 / 52 / 47 / 42 等
- 综合评分与研判 (偏多 / 中性 / 偏空 / 强烈减仓)
- 监控模式 + 信号日志

## 环境

- Python 3.7+
- **无需安装第三方库**（仅标准库）

## 快速开始

```bash
cd ~/Desktop/jinghe-tracker
python3 tracker.py                  # 默认使用同花顺数据
python3 tracker.py --source ths     # 同上
python3 tracker.py --open-ths       # 浏览器打开同花顺个股页
```

## 数据源

| 来源 | 命令 | 说明 |
|------|------|------|
| **同花顺**（默认） | `--source ths` | 同花顺网页端公开 API，**免费，无需账号** |
| 东方财富 | `--source eastmoney` | 备用数据源 |
| iFinD 官方 | `--source ifind` | 需 iFinD 付费账号 + SDK |
| 自动 | `--source auto` | 有 iFinD 则用 iFinD，否则同花顺 |

### 接入同花顺 iFinD（官方，付费）

1. 在 [同花顺数据接口](https://quantapi.10jqka.com.cn/) 申请试用/正式账号  
2. 安装 iFinD 终端，运行 SDK 安装脚本安装 `iFinDPy`  
3. 在 `ths_config.py` 中设置 `IFIND.enabled = True` 并填写账号，或：

```bash
export IFIND_USER=你的账号
export IFIND_PASS=你的密码
python3 tracker.py --source ifind
```

iFinD 终端输入 `sc` 可打开「超级命令」自动生成取数代码。

**注意**：同花顺普通炒股 App **没有**开放交易/行情 API；本程序通过同花顺公开行情接口或 iFinD 官方接口取数，**不能**直接下单或读取 App 内自选股。

## 命令

```bash
# 单次分析报告（同花顺）
python3 tracker.py

# JSON 输出（对接自动化）
python3 tracker.py --json

# 盘中每 5 分钟刷新
python3 tracker.py --watch 300

# 离线模式（使用本地缓存）
python3 tracker.py --offline

# 打开同花顺网页版个股
python3 tracker.py --open-ths

# 问财联动（需 Cookie，见下方）
python3 tracker.py --iwencai
python3 tracker.py --open-iwencai
```

## 新增功能（v2）

### 1. 双源对比（默认开启）

每次运行自动对比 **同花顺 vs 东方财富** 的现价、涨跌幅、换手率；近 5 日收盘价偏差超过 0.3% 会预警。

```bash
python3 tracker.py              # 含双源对比
python3 tracker.py --no-compare # 关闭
```

### 2. 问财 (i问财) 联动

```bash
# 浏览器打开问财（无需 Cookie）
python3 tracker.py --open-iwencai

# 程序化查询（需 Cookie）
export IWENCAI_COOKIE='v=xxx; other=yyy'   # 登录 iwencai.com 后 F12 复制
python3 tracker.py --iwencai
python3 tracker.py --iwencai --iwencai-preset flow   # 资金流问句
python3 tracker.py --iwencai --iwencai-preset risk   # 风险问句
```

预设问句：`fundamental` / `flow` / `industry` / `risk`

### 3. 历史快照 CSV

每次运行自动追加一行到 `data/snapshots.csv`（价格、RSI、评分、双源价差、A/H 溢价），便于回溯。

```bash
python3 tracker.py --no-snapshot   # 关闭写入
```

## 配置

编辑 `config.py`:

| 配置项 | 说明 |
|--------|------|
| `LEVELS` | 支撑/压力位 |
| `H_SHARE` | H 股发行价、上市日、汇率 |
| `THRESHOLDS` | RSI、换手率、A/H 溢价阈值 |

## 信号等级

| 等级 | 含义 |
|------|------|
| BUY | 偏多 |
| INFO | 信息 |
| WARN | 预警 |
| SELL | 减仓/出货 |

## 输出文件

- `data/688249_daily.json` — K 线缓存
- `data/alerts.log` — SELL/WARN 信号日志

## 免责声明

本程序仅供学习研究，不构成投资建议。数据来源于公开接口，请以交易所官方行情为准。
