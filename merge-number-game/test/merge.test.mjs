/**
 * 合并逻辑单元测试（Node 下运行：node merge-number-game/test/merge.test.mjs）
 */
import { createBoard, placeTile } from '../js/board.js';
import { resolveMerges } from '../js/merge.js';

let passed = 0;
let failed = 0;

function assert(cond, msg) {
  if (cond) {
    passed++;
    console.log('✓', msg);
  } else {
    failed++;
    console.error('✗', msg);
  }
}

// 三个 1 横排 → 一个 2
{
  const b = createBoard();
  placeTile(b, 0, 0, 1);
  placeTile(b, 0, 1, 1);
  placeTile(b, 0, 2, 1);
  const { board, totalScore } = resolveMerges(b);
  assert(board[0][0] === 2, '三个1合成一个2');
  assert(board[0][1] === 0 && board[0][2] === 0, '其余格清空');
  assert(totalScore > 0, '合并有得分');
}

// 六个 2（2×3 连通块）→ 两个 3
{
  const b = createBoard();
  for (let c = 0; c < 3; c++) {
    placeTile(b, 0, c, 2);
    placeTile(b, 1, c, 2);
  }
  const { board } = resolveMerges(b);
  let threes = 0;
  for (const row of board) for (const v of row) if (v === 3) threes++;
  assert(threes === 2, '六个2合成两个3');
}

// 四个 3 → 一个 4 + 一个 3
{
  const b = createBoard();
  for (let c = 0; c < 4; c++) placeTile(b, 1, c, 3);
  const { board } = resolveMerges(b);
  let fours = 0;
  let threes = 0;
  for (const row of board) {
    for (const v of row) {
      if (v === 4) fours++;
      if (v === 3) threes++;
    }
  }
  assert(fours === 1 && threes === 1, '四个3 → 一个4 + 一个3');
}

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed > 0 ? 1 : 0);
