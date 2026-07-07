import { CONFIG, mergeScore } from './config.js';
import { cloneBoard } from './board.js';

const DIRS = [
  [0, 1],
  [0, -1],
  [1, 0],
  [-1, 0],
];

/**
 * 查找所有四连通相同数字区域
 * @returns {Array<{cells: Array<[number,number]>, value: number}>}
 */
function findRegions(board) {
  const n = board.length;
  const visited = Array.from({ length: n }, () => Array(n).fill(false));
  const regions = [];

  for (let r = 0; r < n; r++) {
    for (let c = 0; c < n; c++) {
      const val = board[r][c];
      if (val === 0 || visited[r][c]) continue;

      const cells = [];
      const stack = [[r, c]];
      visited[r][c] = true;

      while (stack.length) {
        const [cr, cc] = stack.pop();
        cells.push([cr, cc]);
        for (const [dr, dc] of DIRS) {
          const nr = cr + dr;
          const nc = cc + dc;
          if (
            nr >= 0 && nr < n && nc >= 0 && nc < n &&
            !visited[nr][nc] && board[nr][nc] === val
          ) {
            visited[nr][nc] = true;
            stack.push([nr, nc]);
          }
        }
      }

      if (cells.length >= CONFIG.MIN_MERGE) {
        regions.push({ cells, value: val });
      }
    }
  }
  return regions;
}

/**
 * 对单个区域执行三合一：每 3 个合成 1 个 value+1
 * @returns {{ board: number[][], events: object[], score: number } | null}
 */
function mergeRegion(board, region) {
  const { cells, value } = region;
  const mergeGroups = Math.floor(cells.length / CONFIG.MIN_MERGE);
  if (mergeGroups <= 0) return null;

  const next = cloneBoard(board);
  const sorted = [...cells].sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const allCleared = [];

  for (let g = 0; g < mergeGroups; g++) {
    const start = g * CONFIG.MIN_MERGE;
    const group = sorted.slice(start, start + CONFIG.MIN_MERGE);
    const anchor = group[0];
    for (const [r, c] of group) {
      next[r][c] = 0;
      allCleared.push([r, c]);
    }
    next[anchor[0]][anchor[1]] = value + 1;
  }

  return {
    board: next,
    event: {
      from: value,
      to: value + 1,
      groups: mergeGroups,
      cells: allCleared,
      anchor: sorted[0],
    },
  };
}

/**
 * 执行一轮扫描并合并所有可合并区域（单轮）
 */
function mergeOnce(board) {
  const regions = findRegions(board);
  if (regions.length === 0) return null;

  let next = cloneBoard(board);
  const events = [];
  let roundScore = 0;

  // 按值从大到小合并，减少同格冲突
  regions.sort((a, b) => b.value - a.value);

  for (const region of regions) {
    const result = mergeRegion(next, region);
    if (!result) continue;
    next = result.board;
    events.push(result.event);
    roundScore += mergeScore(result.event.to, result.event.groups, 1);
  }

  if (events.length === 0) return null;
  return { board: next, events, score: roundScore };
}

/**
 * 连锁合并直到稳定
 * @returns {{ board, mergeLog, totalScore }}
 */
export function resolveMerges(board) {
  let current = cloneBoard(board);
  const mergeLog = [];
  let totalScore = 0;
  let chain = 0;

  while (true) {
    const result = mergeOnce(current);
    if (!result) break;
    chain++;
    // 连锁加成重算
    let chainScore = 0;
    for (const ev of result.events) {
      chainScore += mergeScore(ev.to, ev.groups, chain);
    }
    totalScore += chainScore;
    current = result.board;
    mergeLog.push({ chain, events: result.events, score: chainScore });
  }

  return { board: current, mergeLog, totalScore };
}

/** 棋盘字符串指纹，用于检测稳定 */
export function boardKey(board) {
  return board.map((r) => r.join(',')).join('|');
}
