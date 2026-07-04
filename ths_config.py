# -*- coding: utf-8 -*-
"""同花顺数据源配置"""

# 同花顺代码: 上海 hs_688249, 深圳 hs_0xxxxx
THS_CODE = "hs_{}".format("688249")

# 公开行情 API（同花顺网页端使用，无需账号）
THS_PUBLIC = {
    "kline_url": "https://d.10jqka.com.cn/v6/line/{code}/01/last.js",
    "intraday_url": "https://d.10jqka.com.cn/v6/time/{code}/last.js",
    "stock_page": "https://stockpage.10jqka.com.cn/{code}/",
    "iwencai_url": "https://www.iwencai.com/unifiedwap/result?w=688249",
}

# iFinD 官方接口（需付费账号，在 iFinD 终端申请）
# 申请: https://quantapi.10jqka.com.cn/ 或 iFinD 终端输入 sc 打开超级命令
IFIND = {
    "enabled": False,
    "username": "",           # 或设环境变量 IFIND_USER
    "password": "",           # 或设环境变量 IFIND_PASS
    "access_token": "",       # HTTP 模式: 环境变量 IFIND_TOKEN
    "stock_code": "688249.SH",  # 同花顺标准代码
    "http_base": "https://quantapi.51ifind.com/api/v1",
}

# 默认数据源: eastmoney | ths | ifind | auto
# auto = 优先 ifind(已配置) > ths > eastmoney
DATA_SOURCE = "ths"
