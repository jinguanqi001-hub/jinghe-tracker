import { CONFIG } from './config.js';

/** 创建空棋盘 */
export function createBoard(size = CONFIG.BOARD_SIZE) {
  return Array.from({ length: size }, () => Array(size).fill(0));
}

/** 棋盘是否已满 */
export function isBoardFull(board) {
  return board.every((row) => row.every((c) => c !== 0));
}

/** 在 (r,c) 放置数字，返回是否成功 */
export function placeTile(board, r, c, value) {
  if (r < 0 || c < 0 || r >= board.length || c >= board[0].length) return false;
  if (board[r][c] !== 0) return false;
  board[r][c] = value;
  return true;
}

/** 本局出现的最大数字 */
export function maxOnBoard(board) {
  let m = 0;
  for (const row of board) {
    for (const v of row) if (v > m) m = v;
  }
  return m;
}

/** 深拷贝棋盘 */
export function cloneBoard(board) {
  return board.map((row) => row.slice());
}
