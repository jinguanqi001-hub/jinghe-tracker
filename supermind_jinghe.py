# -*- coding: utf-8 -*-
"""
晶合688249 SuperMind v9.1 — 75%底仓 + 25%华虹做T (放宽T减仓)
- 底仓(75%): v8趋势逻辑，仅在强卖/清仓信号时变动
- T仓(25%): 以华虹公司(688347)为基准，日内波段加减
- 日线回测用华虹OHLC近似日内T；实盘建议切换分钟频率
"""

SOURCE_CODE = r'''
# ===== 晶合688249 v9.1: 75%底仓 + 25%华虹做T (放宽T减仓) =====
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

REBAL_MIN = 0.04
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
    log.info('晶合 v9.1 75%%底仓+25%%华虹做T (放宽T减仓) init')


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
    """以华虹公司为基准，计算25% T仓目标 (日线OHLC近似日内)"""
    hh = _vol_signals(BENCHMARK, False)
    if not hh or not main_sig:
        return g.t_sleeve, 'T持有', '-'

    score = 0
    notes = []

    # 华虹探底回升 → 晶合T买
    if hh['lo'] <= hh['ma5'] * 1.012 and hh['px'] > hh['op'] and hh['intraday'] > 0.004:
        score += 2
        notes.append('华虹探底回升')
    # 华虹MA10止跌 → 同业联动T买
    if hh['lo'] <= hh['ma10'] * 1.012 and hh['px'] > hh['ma10'] and hh['px'] > hh['op']:
        score += 1
        notes.append('华虹MA10企稳')
    # 华虹RSI超卖反弹
    if hh['rsi'] <= 38 and hh['px'] > hh['op']:
        score += 2
        notes.append('华虹RSI超卖反弹')
    # 华虹放量上影/高潮 → 晶合T卖 (v9.1放宽: 需天量+更长上影)
    if hh['upper'] >= 0.50 and hh['vr'] >= VOL_CLIMAX:
        score -= 2
        notes.append('华虹天量上影')
    if hh['vr'] >= VOL_CLIMAX and hh['px'] < hh['op'] and hh['intraday'] < -0.01:
        score -= 1
        notes.append('华虹放量长阴')
    if hh['rsi'] >= 85:
        score -= 1
        notes.append('华虹RSI超买')
    # 相对强弱: 华虹弱于晶合 → 晶合补涨T买
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

    if score >= 3:
        tgt, act = T_MAX, 'T加满'
    elif score >= 1:
        tgt, act = T_MID, 'T半仓'
    elif score <= -6:
        tgt, act = 0.0, 'T清空'
    else:
        tgt, act = max(g.t_sleeve, T_MID), 'T持有'

    g.t_sleeve = tgt
    return tgt, act, ';'.join(notes) if notes else '-'


def _core_target(mb, ms, lb, hold, uptrend):
    """底仓75%: 仅在建仓/清仓时变动，中间不动"""
    if ms <= -8:
        g.core_on = False
        return 0.0, '底仓清仓'

    if not g.core_on:
        if mb >= 2 or lb >= LEADER_BUY_MIN:
            g.core_on = True
            return CORE_PCT, '底仓建仓'
        if mb >= 1 and uptrend:
            g.core_on = True
            return CORE_PCT, '底仓趋势建仓'
        return 0.0, '空仓'

    # 已持底仓 — 不动，除非极端破位
    if ms <= -6 and not uptrend:
        g.core_on = False
        return 0.0, '底仓破位清仓'
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

    core_tgt, core_act = _core_target(mb, ms, lb, hold, main['uptrend'])
    t_tgt, t_act, t_note = _hh_t_sleeve(context, main)

    if core_tgt <= 0:
        tgt = 0.0
        action = core_act
        g.t_sleeve = T_MID
    else:
        t_tgt = max(t_tgt, T_MID)  # 底仓在时T永不低于12.5%
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
