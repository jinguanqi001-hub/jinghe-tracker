# -*- coding: utf-8 -*-
"""
晶合688249 SuperMind
- v9.3 SOURCE_CODE: 75%底仓 + 25%华虹大波段做T (日线频率，T为OHLC近似)
- v10 INTRADAY_SOURCE_CODE: 75%底仓 + 25%华虹日内T (MINUTE频率，分钟级华虹信号)
"""

SOURCE_CODE = r'''
# ===== 晶合688249 v9.3: 75%底仓 + 25%华虹大波段做T =====
STOCK = '688249.SH'
BENCHMARK = '688347.SH'   # 华虹公司 — T仓基准

CORE_PCT = 0.75           # 底仓比例（不动）
T_MAX = 0.25              # T仓上限
T_MID = 0.125             # T仓中性

LEADERS = {
    '688347.SH': 1.2,
    '688361.SH': 1.0,
    '688082.SH': 1.0,
}

REBAL_MIN = 0.015
LEADER_BUY_MIN = 2

R67 = 67.0
R61 = 61.0
S58 = 58.0
S52 = 52.0
VOL_BREAK = 1.30
VOL_STRONG = 1.55
VOL_CLIMAX = 1.90
VOL_PANIC = 1.45
SHADOW_RATIO = 0.50


def init(context):
    g.stock = STOCK
    context.security = STOCK
    g.r67_fail = 0
    g.last_target = -1.0
    g.core_on = False
    g.t_sleeve = T_MID
    log.info('晶合 v9.3 75%%底仓+25%%华虹大波段做T init')


def _rsi(closes, n=14):
    if len(closes) < n + 1:
        return 50.0
    gs, ls = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gs.append(max(d, 0))
        ls.append(max(-d, 0))
    ag = sum(gs[-n:]) / n
    al = sum(ls[-n:]) / n
    if al == 0:
        return 100.0
    rs = ag / al
    return 100 - 100 / (1 + rs)


def _vol_signals(symbol, use_levels):
    df = history(
        symbol,
        ['open', 'high', 'low', 'close', 'volume'],
        35,
        '1d',
        False,
        'pre',
        True,
    )
    if df is None or len(df) < 22:
        return None

    o = list(df['open'])
    h = list(df['high'])
    l = list(df['low'])
    c = list(df['close'])
    v = list(df['volume'])

    px = c[-1]
    hi = h[-1]
    lo = l[-1]
    op = o[-1]
    prev = c[-2]
    prev2 = c[-3]

    ma5 = sum(c[-5:]) / 5
    ma10 = sum(c[-10:]) / 10
    ma20 = sum(c[-20:]) / 20
    rsi = _rsi(c)
    uptrend = px > ma20 and ma5 > ma10 > ma20

    vma5 = sum(v[-6:-1]) / 5 if len(v) >= 6 else float(v[-1] or 1)
    if vma5 <= 0:
        vma5 = 1.0
    vr = float(v[-1] or 0) / vma5
    denom = sum(v[-7:-2]) / 5 if len(v) >= 7 else vma5
    if denom <= 0:
        denom = 1.0
    vr_prev = float(v[-2] or 0) / denom

    body = abs(px - op) if abs(px - op) > 0.01 else 0.01
    upper = (hi - max(op, px)) / body
    chg = (px - prev) / prev if prev else 0.0
    intraday = (px - op) / op if op else 0.0

    buy = 0
    sell = 0
    br, sr = [], []

    if use_levels:
        if px > S58 and prev <= S58 * 1.005 and vr >= VOL_BREAK:
            buy += 3
            br.append('58平台放量突破')
        if px > S52 and prev2 <= S52 * 1.01 and prev > S52 * 0.995 and vr >= VOL_BREAK:
            buy += 2
            br.append('52放量再突破')
        if px >= R61 * 0.98 and vr >= VOL_STRONG and upper >= 0.35:
            sell -= 2 if not uptrend else 1
            sr.append('61区放量上影')
        if hi >= R67 * 0.985 and px < R67 * 0.992 and vr >= VOL_BREAK:
            sell -= 3 if not uptrend else 1
            sr.append('67放量回落')
        if px < S58 * 0.993 and px < op and chg < 0 and vr >= VOL_PANIC and max(c[-20:]) >= S58 * 0.95:
            sell -= 3
            sr.append('破58放量阴')
        if px < S52 * 0.995 and px < op and chg < 0 and vr >= VOL_PANIC and max(c[-20:]) >= S52 * 0.95:
            sell -= 4
            sr.append('破52放量阴')

    if px > ma20 and ma5 > ma10 and vr >= VOL_BREAK and px > op and chg > 0:
        buy += 1
        br.append('趋势放量阳')
    if px > ma20 and vr_prev < 0.85 and vr >= VOL_STRONG and px > op:
        buy += 3
        br.append('缩量后放量反弹')
    if lo <= ma10 * 1.012 and px > ma10 and vr >= VOL_BREAK and px > op:
        buy += 2
        br.append('MA10放量止跌')
    if px > ma5 > ma10 > ma20 and 1.05 <= vr <= 1.7:
        buy += 1
        br.append('多头温和放量')
    if uptrend and lo <= ma20 * 1.015 and px > ma20 and px > op:
        buy += 3
        br.append('MA20回踩')
    if prev < ma10 and px > ma10 and px > op and vr >= VOL_BREAK:
        buy += 4
        br.append('V型反转')
    ret5 = (px - c[-6]) / c[-6] if len(c) >= 6 and c[-6] else 0.0
    if ret5 >= 0.10 and px > ma5 and px > op:
        buy += 3
        br.append('5日动量')

    if vr >= VOL_CLIMAX and upper >= SHADOW_RATIO:
        sell -= 3 if not uptrend else 1
        sr.append('放量长上影')
    if vr >= VOL_CLIMAX and px < op:
        sell -= 3 if not uptrend else 2
        sr.append('放量阴线')
    if vr >= VOL_CLIMAX and abs(chg) < 0.008:
        sell -= 2 if not uptrend else 1
        sr.append('天量滞涨')
    if px < ma10 and prev >= ma10 and px < op and vr >= VOL_PANIC:
        sell -= 2
        sr.append('放量破MA10阴')
    if px < ma20 and prev < ma20 and px < op and vr >= VOL_PANIC:
        sell -= 4
        sr.append('放量破MA20阴')
    if rsi >= 85 and vr >= VOL_STRONG and not uptrend:
        sell -= 1
        sr.append('RSI高+放量')

    return {
        'buy': buy,
        'sell': sell,
        'br': ';'.join(br),
        'sr': ';'.join(sr),
        'vr': vr,
        'px': px,
        'uptrend': uptrend,
        'rsi': rsi,
        'intraday': intraday,
        'upper': upper,
        'ma5': ma5,
        'ma10': ma10,
        'ma20': ma20,
        'op': op,
        'lo': lo,
    }


def _analyze_main(context):
    sig = _vol_signals(g.stock, True)
    if not sig:
        return None
    df = history(g.stock, ['high', 'close'], 5, '1d', False, 'pre', True)
    if df is not None and len(df) >= 2:
        hi = float(list(df['high'])[-1])
        px = float(list(df['close'])[-1])
        if hi >= R67 * 0.985 and px < R67 * 0.995:
            g.r67_fail += 1
        else:
            g.r67_fail = max(0, g.r67_fail - 1)
        if g.r67_fail >= 3 and px >= 62.0:
            sig['sell'] -= 2 if not sig['uptrend'] else 1
            sig['sr'] = (sig['sr'] + ';67三重顶').strip(';')
    return sig


def _analyze_leaders(context):
    lb = 0.0
    ls = 0.0
    lbr, lsr = [], []
    for code, wt in LEADERS.items():
        sig = _vol_signals(code, False)
        if not sig:
            continue
        if sig['buy'] >= 2:
            lb += 2 * wt
            lbr.append(code[-7:-3] + '买')
        if sig['sell'] <= -3:
            ls -= 3 * wt
            lsr.append(code[-7:-3] + '卖')
    return int(round(lb)), int(round(ls)), ';'.join(lbr), ';'.join(lsr)


def _hh_t_sleeve(context, main_sig):
    """v9.3 华虹T: score≥2加满 / score≤-2全出 / 其余持有"""
    hh = _vol_signals(BENCHMARK, False)
    if not hh or not main_sig:
        return g.t_sleeve, 'T持有', '-'

    score = 0
    notes = []
    if hh['lo'] <= hh['ma5'] * 1.012 and hh['px'] > hh['op'] and hh['intraday'] > 0.004:
        score += 2
        notes.append('华虹探底回升')
    if hh['lo'] <= hh['ma10'] * 1.012 and hh['px'] > hh['ma10'] and hh['px'] > hh['op']:
        score += 1
        notes.append('华虹MA10企稳')
    if hh['rsi'] <= 38 and hh['px'] > hh['op']:
        score += 2
        notes.append('华虹RSI超卖反弹')
    if hh['upper'] >= 0.50 and hh['vr'] >= VOL_CLIMAX:
        score -= 2
        notes.append('华虹天量上影')
    if hh['vr'] >= VOL_CLIMAX and hh['px'] < hh['op'] and hh['intraday'] < -0.01:
        score -= 1
        notes.append('华虹放量长阴')
    if hh['rsi'] >= 85:
        score -= 1
        notes.append('华虹RSI超买')
    hh_prev = history(BENCHMARK, ['close'], 2, '1d', False, 'pre', True)
    jh_prev = history(g.stock, ['close'], 2, '1d', False, 'pre', True)
    if hh_prev is not None and jh_prev is not None and len(hh_prev) >= 2 and len(jh_prev) >= 2:
        hh_c = list(hh_prev['close'])
        jh_c = list(jh_prev['close'])
        hh_chg = (hh_c[-1] - hh_c[-2]) / hh_c[-2] if hh_c[-2] else 0.0
        jh_chg = (jh_c[-1] - jh_c[-2]) / jh_c[-2] if jh_c[-2] else 0.0
        if hh_chg < -0.01 and jh_chg > hh_chg + 0.005:
            score += 1
            notes.append('华虹弱晶合强')
        if hh_chg > 0.03 and jh_chg < hh_chg - 0.015:
            score -= 1
            notes.append('华虹强晶合弱')

    if score >= 2:
        tgt, act = T_MAX, 'T加满'
    elif score <= -2:
        tgt, act = 0.0, 'T全出'
    else:
        tgt, act = g.t_sleeve, 'T持有'

    g.t_sleeve = tgt
    return tgt, act, ';'.join(notes) if notes else '-'


def _core_target(mb, ms, lb, main_sig):
    """v9.2 底仓：快入慢出，仅三重确认清仓"""
    px, op = main_sig['px'], main_sig['op']
    ma20_val = main_sig.get('ma20', main_sig['ma10'])
    if ms <= -8 and px < ma20_val and px < op:
        g.core_on = False
        return 0.0, '底仓清仓'

    if not g.core_on:
        if mb >= 1 or main_sig['uptrend'] or px > ma20_val or lb >= LEADER_BUY_MIN:
            g.core_on = True
            return CORE_PCT, '底仓建仓'
        return 0.0, '空仓'

    return CORE_PCT, '底仓持有'


def handle_bar(context, bar_dict):
    main = _analyze_main(context)
    if not main:
        return

    lb, ls, lbr, lsr = _analyze_leaders(context)
    mb, ms = main['buy'], main['sell']

    pos = context.portfolio.positions.get(g.stock)
    hold = pos.amount if pos else 0
    price = bar_dict[g.stock].close
    total = context.portfolio.total_value
    pos_pct = (pos.market_value / total) if (pos and total > 0) else 0.0

    core_tgt, core_act = _core_target(mb, ms, lb, main)
    t_tgt, t_act, t_note = _hh_t_sleeve(context, main)

    if core_tgt <= 0:
        tgt = 0.0
        action = core_act
        g.t_sleeve = T_MAX
    else:
        tgt = min(core_tgt + t_tgt, 1.0)
        action = '{}+{}'.format(core_act, t_act)

    log.info(
        '{} px={:.2f} 底={:.0%} T={:.0%} 总={:.0%} {} | m={}/{} | 华虹T:{} | {} / {} | 领先:{}'.format(
            get_datetime(), price, core_tgt, t_tgt, tgt, action,
            mb, ms, t_note, main['br'] or '-', main['sr'] or '-', lbr or '-',
        )
    )

    if abs(pos_pct - tgt) < REBAL_MIN and hold > 0:
        return
    if tgt == 0.0 and hold == 0:
        return

    if abs(g.last_target - tgt) >= REBAL_MIN or (tgt == 0 and hold > 0) or (tgt > 0 and hold == 0):
        order_target_percent(g.stock, tgt)
        g.last_target = tgt
        log.info('调仓 -> {:.0%} (底{:.0%}+T{:.0%})'.format(tgt, core_tgt, t_tgt))
'''

# ===== v10 日内T — SuperMind 分钟频率 =====
# 用法: research_strategy(INTRADAY_SOURCE_CODE, frequency='MINUTE', ...)
# 底仓75%仍用日线趋势；T仓25%用华虹分钟级信号 0↔25%
INTRADAY_SOURCE_CODE = r'''
# ===== 晶合688249 v10.1: 75%底仓 + 25%华虹日内T (分钟级) =====
STOCK = '688249.SH'
BENCHMARK = '688347.SH'

CORE_PCT = 0.75
T_MAX = 0.25
T_MID = 0.125
REBAL_MIN = 0.015
MIN_TRADE_GAP = 10         # 分钟，T仓最短调仓间隔

# v10.1 日内T阈值 — 减频 + 趋势保护
PULLBACK_BUY = 0.015
BOUNCE_BUY = 0.005
SPIKE_SELL = 0.022
DROP_SELL = 0.010
RSI_OS = 35
RSI_OB = 72
REL_GAP = 0.008
BUY_FULL = 3
BUY_MID = 2
SELL_CUT = -2
SELL_CLEAR = -3
SELL_FORCE = -4


def init(context):
    g.stock = STOCK
    context.security = STOCK
    g.core_on = True
    g.t_sleeve = T_MAX
    g.last_t_bar = -999
    g.last_core_day = None
    g.uptrend = True
    log.info('晶合 v10.1 75%%底仓+25%%华虹日内T (MINUTE) init')


def _rsi(closes, n=14):
    if len(closes) < n + 1:
        return 50.0
    gs, ls = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gs.append(max(d, 0))
        ls.append(max(-d, 0))
    ag = sum(gs[-n:]) / n
    al = sum(ls[-n:]) / n
    if al == 0:
        return 100.0
    return 100 - 100 / (1 + ag / al)


def _daily_core(context):
    """底仓：日线趋势，每日开盘更新一次"""
    dt = get_datetime()
    day_key = dt.strftime('%Y%m%d') if dt else ''
    if g.last_core_day == day_key:
        return CORE_PCT if g.core_on else 0.0

    df = history(g.stock, ['open', 'high', 'low', 'close', 'volume'], 25, '1d', False, 'pre', True)
    if df is None or len(df) < 20:
        g.last_core_day = day_key
        return CORE_PCT if g.core_on else 0.0

    c = list(df['close'])
    px = c[-1]
    ma20 = sum(c[-20:]) / 20
    ma5 = sum(c[-5:]) / 5
    ma10 = sum(c[-10:]) / 10
    uptrend = px > ma20 and ma5 > ma10 > ma20

    if not g.core_on and (uptrend or px > ma20):
        g.core_on = True
    if g.core_on and px < ma20 * 0.97 and px < list(df['open'])[-1]:
        g.core_on = False

    g.uptrend = uptrend
    g.last_core_day = day_key
    return CORE_PCT if g.core_on else 0.0


def _intraday_stats(symbol, n=60):
    """当日分钟线统计"""
    df = history(symbol, ['open', 'high', 'low', 'close', 'volume'], n, '1m', False, 'pre', True)
    if df is None or len(df) < 3:
        return None
    o = list(df['open'])
    h = list(df['high'])
    l = list(df['low'])
    c = list(df['close'])
    px = c[-1]
    prev = c[-2]
    op = o[0]
    hi = max(h)
    lo = min(l)
    vwap = sum(c) / len(c)
    pullback = (hi - px) / hi if hi else 0.0
    bounce = (px - lo) / lo if lo else 0.0
    intraday = (px - op) / op if op else 0.0
    rsi_val = _rsi(c[-min(20, len(c)):])
    return {
        'px': px, 'prev': prev, 'op': op, 'hi': hi, 'lo': lo,
        'vwap': vwap, 'pullback': pullback, 'bounce': bounce,
        'intraday': intraday, 'rsi': rsi_val, 'closes': c,
    }


def _hh_intraday_t(context, bar_idx):
    """v10.1 华虹分钟T: 分级调仓 + 趋势保护"""
    hh = _intraday_stats(BENCHMARK, 60)
    jh = _intraday_stats(g.stock, 60)
    if not hh or not jh:
        return g.t_sleeve, 'T持有', '-'

    score = 0
    notes = []
    px, prev, vwap = hh['px'], hh['prev'], hh['vwap']
    op, intraday = hh['op'], hh['intraday']
    t_min = T_MID if g.uptrend else 0.0

    if hh['pullback'] >= PULLBACK_BUY and px > prev and px >= vwap * 0.998:
        score += 2
        notes.append('华虹日内回落后回升')
    if hh['bounce'] >= BOUNCE_BUY and px > op and px > prev:
        score += 1
        notes.append('华虹自低点反弹')
    if hh['rsi'] <= RSI_OS and px > prev and px > vwap:
        score += 2
        notes.append('华虹分钟RSI超卖反弹')
    if px <= hh['lo'] * 1.005 and px > prev:
        score += 1
        notes.append('华虹接近日内低点转强')

    if hh['bounce'] >= SPIKE_SELL and px < prev and px < vwap:
        score -= 2
        notes.append('华虹日内拉升后转弱')
    if hh['pullback'] >= DROP_SELL and px < prev and intraday < 0:
        score -= 1
        notes.append('华虹自高点回落')
    if hh['rsi'] >= RSI_OB and px < prev:
        score -= 1
        notes.append('华虹分钟RSI超买')
    if px > vwap * 1.012 and px < prev and intraday > 0.01:
        score -= 1
        notes.append('华虹偏离VWAP回落')

    gap = jh['intraday'] - intraday
    if gap >= REL_GAP:
        score += 1
        notes.append('晶合强于华虹')
    if gap <= -REL_GAP and intraday > 0.015:
        score -= 1
        notes.append('华虹强于晶合')

    if score >= BUY_FULL:
        tgt, act = T_MAX, 'T加满'
    elif score >= BUY_MID:
        tgt = max(T_MID, t_min)
        act = 'T半仓加' if g.t_sleeve < T_MAX else 'T持有'
        if g.t_sleeve >= T_MAX:
            tgt = g.t_sleeve
    elif score <= SELL_CLEAR:
        if g.uptrend and score > SELL_FORCE:
            tgt, act = T_MID, '趋势T保护'
        else:
            tgt, act = t_min, 'T全出'
    elif score <= SELL_CUT:
        tgt = max(T_MID, t_min)
        act = 'T半仓减' if g.t_sleeve > t_min else 'T持有'
        if g.t_sleeve <= t_min:
            tgt = g.t_sleeve
    else:
        tgt, act = g.t_sleeve, 'T持有'

    if bar_idx - g.last_t_bar >= MIN_TRADE_GAP or act not in ('T持有',):
        if tgt != g.t_sleeve:
            g.t_sleeve = tgt
            g.last_t_bar = bar_idx

    return g.t_sleeve, act, ';'.join(notes) if notes else '-'


def handle_bar(context, bar_dict):
    bar_idx = getattr(context, 'current_dt', None)
    idx = bar_idx.minute if bar_idx else 0

    core_tgt = _daily_core(context)
    t_tgt, t_act, t_note = _hh_intraday_t(context, idx)

    pos = context.portfolio.positions.get(g.stock)
    hold = pos.amount if pos else 0
    price = bar_dict[g.stock].close
    total = context.portfolio.total_value
    pos_pct = (pos.market_value / total) if (pos and total > 0) else 0.0

    if core_tgt <= 0:
        tgt = 0.0
        action = '底仓清仓'
        g.t_sleeve = T_MAX
    else:
        tgt = min(core_tgt + t_tgt, 1.0)
        action = '底仓持有+{}'.format(t_act)

    log.info(
        '{} px={:.2f} 底={:.0%} T={:.0%} 总={:.0%} {} | 华虹T:{}'.format(
            get_datetime(), price, core_tgt, t_tgt, tgt, action, t_note,
        )
    )

    if abs(pos_pct - tgt) < REBAL_MIN and hold > 0:
        return
    if tgt == 0.0 and hold == 0:
        return

    order_target_percent(g.stock, tgt)
    log.info('日内T调仓 -> {:.0%}'.format(tgt))
'''
