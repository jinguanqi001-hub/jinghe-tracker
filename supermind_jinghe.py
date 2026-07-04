# -*- coding: utf-8 -*-
"""
晶合688249 SuperMind v7.2 — 量价 + 领先股仅建仓
- 领先买 ≥3 仅空仓建仓加分 | 卖出仅看晶合 | 仓位变化 <8% 不调仓
"""

SOURCE_CODE = r'''
# ===== 晶合688249 v7.2: 量价 + 领先股仅建仓 =====
STOCK = '688249.SH'

LEADERS = {
    '688347.SH': 1.2,
    '688361.SH': 1.0,
    '688082.SH': 1.0,
}

REBAL_MIN = 0.08
LEADER_BUY_MIN = 3

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
    log.info('晶合 v7.2 领先股仅建仓 init')


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
            sell -= 2
            sr.append('61区放量上影')
        if hi >= R67 * 0.985 and px < R67 * 0.992 and vr >= VOL_BREAK:
            sell -= 3
            sr.append('67放量回落')
        if px < S58 * 0.993 and vr >= VOL_PANIC and max(c[-20:]) >= S58 * 0.95:
            sell -= 3
            sr.append('破58放量')
        if px < S52 * 0.995 and vr >= VOL_PANIC and max(c[-20:]) >= S52 * 0.95:
            sell -= 4
            sr.append('破52放量')

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

    if vr >= VOL_CLIMAX and upper >= SHADOW_RATIO:
        sell -= 3
        sr.append('放量长上影')
    if vr >= VOL_CLIMAX and px < op:
        sell -= 3
        sr.append('放量阴线')
    if vr >= VOL_CLIMAX and abs(chg) < 0.008:
        sell -= 2
        sr.append('天量滞涨')
    if px < ma10 and prev >= ma10 and vr >= VOL_PANIC:
        sell -= 2
        sr.append('放量破MA10')
    if px < ma20 and prev < ma20 and vr >= VOL_PANIC:
        sell -= 4
        sr.append('放量破MA20')
    if rsi >= 78 and vr >= VOL_STRONG:
        sell -= 1
        sr.append('RSI高+放量')

    return {
        'buy': buy,
        'sell': sell,
        'br': ';'.join(br),
        'sr': ';'.join(sr),
        'vr': vr,
        'px': px,
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
        if g.r67_fail >= 2 and px >= 59.0:
            sig['sell'] -= 2
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


def _merge_target(mb, ms, lb, hold):
    buy = mb
    sell = ms

    if sell <= -6:
        return 0.0, '清仓'
    if sell <= -4:
        return 0.25, '重度减仓'
    if sell <= -2:
        return 0.55, '轻度减仓'
    if buy >= 4:
        return 0.95, '强买'
    if buy >= 3:
        return 0.90, '强买'
    if buy >= 2:
        return 0.75, '买入加仓'
    if buy >= 1:
        return 0.85, '偏多持有'
    if buy + sell <= -1:
        return 0.60, '偏空降仓'
    if hold <= 0 and mb == 0 and lb >= LEADER_BUY_MIN:
        return 0.75, '领先指引建仓'
    return None, '观望'


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

    tgt, action = _merge_target(mb, ms, lb, hold)
    if tgt is None:
        log.info(
            '{} px={:.2f} vr={:.2f} m={}/{} L={}/{} pos={:.0%} 观望'.format(
                get_datetime(), price, main['vr'], mb, ms, lb, ls, pos_pct
            )
        )
        return

    log.info(
        '{} px={:.2f} m={}/{} L={}/{} -> {:.0%} {} | {} / {} | 领先:{} / {}'.format(
            get_datetime(), price, mb, ms, lb, ls, tgt, action,
            main['br'] or '-', main['sr'] or '-', lbr or '-', lsr or '-',
        )
    )

    if abs(pos_pct - tgt) < REBAL_MIN and hold > 0:
        return
    if tgt == 0.0 and hold == 0:
        return

    if abs(g.last_target - tgt) >= REBAL_MIN or (tgt == 0 and hold > 0) or (tgt > 0 and hold == 0):
        order_target_percent(g.stock, tgt)
        g.last_target = tgt
        log.info('调仓 -> {:.0%} ({})'.format(tgt, action))
'''
