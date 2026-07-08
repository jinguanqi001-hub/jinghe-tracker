# -*- coding: utf-8 -*-
"""晶合集成 (688249) 量化跟踪配置"""

STOCK_CODE = "688249"
STOCK_NAME = "晶合集成"
# 东方财富 secid: 1=上海, 0=深圳
SECID = "1.688249"

# 仓位结构 (v9: 75%底仓 + 25%华虹做T)
POSITION = {
    "core_pct": 0.75,       # 底仓 — 趋势持有不动
    "t_max_pct": 0.25,      # T仓上限
    "t_mid_pct": 0.125,     # T仓中性
}

# 做T基准股 — 华虹公司
BENCHMARK = {
    "code": "688347",
    "name": "华虹公司",
    "secid": "1.688347",
}

# 关键价位（可根据策略调整）
LEVELS = {
    "strong_resistance": 67.0,   # 三重顶压力
    "resistance": 61.0,          # 短期争夺区
    "platform_support": 58.0,    # 6月平台
    "breakout_base": 52.0,       # 6月突破起点
    "limit_up_support": 47.0,    # 5月涨停支撑
    "price_hike_level": 42.0,    # 提价日区域
    "panic_low": 38.0,           # 5月恐慌低点
    "annual_low": 26.0,          # 3月底部
}

# H股相关（用于溢价监控，港元发行价区间）
H_SHARE = {
    "listing_date": "2026-07-10",
    "price_low_hkd": 30.0,
    "price_high_hkd": 32.30,
    "hkd_cny_rate": 0.92,  # 近似汇率，可手动更新
}

# 信号阈值
THRESHOLDS = {
    "ma_short": 5,
    "ma_mid": 10,
    "ma_long": 20,
    "rsi_period": 14,
    "rsi_overbought": 85,
    "rsi_oversold": 30,
    "volume_climax_turnover": 4.0,      # 换手率% 高潮阈值
    "volume_normal_turnover": 2.5,
    "upper_shadow_ratio": 0.5,          # 上影线/实体 出货判定
    "ma_deviation_warning": 0.15,         # 偏离20日线15%预警
    "ah_premium_warning": 0.80,           # A/H溢价超80%预警
}

# 数据
HISTORY_DAYS = 120
DATA_CACHE_DIR = "data"
ALERT_LOG = "data/alerts.log"

# 数据源: ths(同花顺) | eastmoney | ifind | auto
try:
    from ths_config import DATA_SOURCE
except ImportError:
    DATA_SOURCE = "ths"
