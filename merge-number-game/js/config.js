/** 游戏全局配置 */
export const CONFIG = {
  BOARD_SIZE: 5,
  MIN_MERGE: 3,

  // 待放置数字池 [值, 权重]
  SPAWN_POOL: [
    [1, 50],
    [2, 35],
    [3, 15],
  ],

  // 数字对应颜色（等级从 1 起）
  COLORS: {
    1: '#74b9ff',
    2: '#0984e3',
    3: '#00cec9',
    4: '#00b894',
    5: '#55efc4',
    6: '#fdcb6e',
    7: '#e17055',
    8: '#ff7675',
    9: '#e84393',
    10: '#a29bfe',
    11: '#6c5ce7',
    12: '#fd79a8',
  },
  DEFAULT_COLOR: '#ffeaa7',

  // 布局（逻辑像素，按屏幕缩放）
  PADDING: 16,
  HEADER_H: 72,
  FOOTER_H: 120,
  CELL_GAP: 6,
  CELL_RADIUS: 10,

  BG_TOP: '#1a1a2e',
  BG_BOTTOM: '#16213e',
  EMPTY_CELL: 'rgba(255,255,255,0.08)',
  EMPTY_BORDER: 'rgba(255,255,255,0.15)',
  TEXT: '#ffffff',
  TEXT_DIM: 'rgba(255,255,255,0.6)',

  ANIM_MS: 280,
  STORAGE_KEY: 'merge_number_best',
};

/** 按权重随机抽取待放置数字 */
export function rollNextTile(unlockedExtra = false) {
  const pool = CONFIG.SPAWN_POOL.filter(([, w]) => w > 0);
  if (unlockedExtra) pool.push([4, 5]);
  const total = pool.reduce((s, [, w]) => s + w, 0);
  let r = Math.random() * total;
  for (const [val, w] of pool) {
    r -= w;
    if (r <= 0) return val;
  }
  return pool[0][0];
}

/** 数字显示颜色 */
export function colorForValue(v) {
  if (CONFIG.COLORS[v]) return CONFIG.COLORS[v];
  const keys = Object.keys(CONFIG.COLORS).map(Number);
  const max = Math.max(...keys);
  return CONFIG.COLORS[max] || CONFIG.DEFAULT_COLOR;
}

/** 合并得分 */
export function mergeScore(newValue, groupCount, chainIndex) {
  const chainBonus = 1 + 0.1 * Math.max(0, chainIndex - 1);
  return Math.round(newValue * groupCount * chainBonus);
}
