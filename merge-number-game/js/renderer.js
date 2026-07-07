import { CONFIG, colorForValue } from './config.js';

export class Renderer {
  constructor(canvas, ctx, screenW, screenH) {
    this.canvas = canvas;
    this.ctx = ctx;
    this.w = screenW;
    this.h = screenH;
    this.layout = this._calcLayout();
    this.animations = [];
  }

  resize(screenW, screenH) {
    this.w = screenW;
    this.h = screenH;
    this.layout = this._calcLayout();
  }

  _calcLayout() {
    const { PADDING, HEADER_H, FOOTER_H, CELL_GAP } = CONFIG;
    const boardAreaH = this.h - HEADER_H - FOOTER_H - PADDING * 2;
    const boardAreaW = this.w - PADDING * 2;
    const size = CONFIG.BOARD_SIZE;
    const cellSize = Math.floor(
      Math.min(boardAreaW, boardAreaH) / size - CELL_GAP
    );
    const boardW = cellSize * size + CELL_GAP * (size - 1);
    const boardH = boardW;
    const boardX = (this.w - boardW) / 2;
    const boardY = HEADER_H + PADDING + (boardAreaH - boardH) / 2;

    return {
      cellSize,
      boardX,
      boardY,
      boardW,
      boardH,
      previewY: boardY + boardH + 36,
      btnY: this.h - FOOTER_H + 24,
    };
  }

  /** 屏幕坐标 → 格子索引，无效返回 null */
  hitCell(x, y) {
    const { boardX, boardY, cellSize, boardW, boardH } = this.layout;
    if (x < boardX || y < boardY || x > boardX + boardW || y > boardY + boardH) {
      return null;
    }
    const size = CONFIG.BOARD_SIZE;
    const gap = CONFIG.CELL_GAP;
    const localX = x - boardX;
    const localY = y - boardY;
    const c = Math.floor(localX / (cellSize + gap));
    const r = Math.floor(localY / (cellSize + gap));
    if (r < 0 || c < 0 || r >= size || c >= size) return null;
    const inCellX = localX - c * (cellSize + gap);
    const inCellY = localY - r * (cellSize + gap);
    if (inCellX > cellSize || inCellY > cellSize) return null;
    return { r, c };
  }

  hitRestart(x, y) {
    const btn = this._restartBtn();
    return x >= btn.x && x <= btn.x + btn.w && y >= btn.y && y <= btn.y + btn.h;
  }

  hitShare(x, y) {
    const btn = this._shareBtn();
    return x >= btn.x && x <= btn.x + btn.w && y >= btn.y && y <= btn.y + btn.h;
  }

  hitPlayAgain(x, y) {
    if (!this._gameOver) return false;
    const btn = this._playAgainBtn();
    return x >= btn.x && x <= btn.x + btn.w && y >= btn.y && y <= btn.y + btn.h;
  }

  _restartBtn() {
    const w = 120;
    const h = 40;
    return { x: this.w / 2 - w - 12, y: this.layout.btnY, w, h };
  }

  _shareBtn() {
    const w = 120;
    const h = 40;
    return { x: this.w / 2 + 12, y: this.layout.btnY, w, h };
  }

  _playAgainBtn() {
    const w = 160;
    const h = 44;
    return { x: (this.w - w) / 2, y: this.h / 2 + 60, w, h };
  }

  setGameOver(v) {
    this._gameOver = v;
  }

  pushAnim(type, payload) {
    this.animations.push({
      type,
      payload,
      start: Date.now(),
      duration: CONFIG.ANIM_MS,
    });
  }

  _roundRect(x, y, w, h, r) {
    const ctx = this.ctx;
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
  }

  _drawBg() {
    const ctx = this.ctx;
    const g = ctx.createLinearGradient(0, 0, 0, this.h);
    g.addColorStop(0, CONFIG.BG_TOP);
    g.addColorStop(1, CONFIG.BG_BOTTOM);
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, this.w, this.h);
  }

  _drawHeader(score, best) {
    const ctx = this.ctx;
    ctx.fillStyle = CONFIG.TEXT;
    ctx.font = 'bold 22px sans-serif';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.fillText(`分数 ${score}`, CONFIG.PADDING, 24);
    ctx.textAlign = 'right';
    ctx.fillStyle = CONFIG.TEXT_DIM;
    ctx.font = '18px sans-serif';
    ctx.fillText(`最高 ${best}`, this.w - CONFIG.PADDING, 28);
  }

  _cellRect(r, c) {
    const { boardX, boardY, cellSize } = this.layout;
    const gap = CONFIG.CELL_GAP;
    return {
      x: boardX + c * (cellSize + gap),
      y: boardY + r * (cellSize + gap),
      w: cellSize,
      h: cellSize,
    };
  }

  _drawCell(r, c, value, alpha = 1, scale = 1) {
    const rect = this._cellRect(r, c);
    const ctx = this.ctx;
    const cx = rect.x + rect.w / 2;
    const cy = rect.y + rect.h / 2;
    const sw = rect.w * scale;
    const sh = rect.h * scale;

    ctx.save();
    ctx.globalAlpha = alpha;
    this._roundRect(cx - sw / 2, cy - sh / 2, sw, sh, CONFIG.CELL_RADIUS);

    if (value === 0) {
      ctx.fillStyle = CONFIG.EMPTY_CELL;
      ctx.fill();
      ctx.strokeStyle = CONFIG.EMPTY_BORDER;
      ctx.lineWidth = 1;
      ctx.stroke();
    } else {
      ctx.fillStyle = colorForValue(value);
      ctx.fill();
      ctx.fillStyle = CONFIG.TEXT;
      const fontSize = Math.max(14, Math.min(28, rect.w * 0.42));
      ctx.font = `bold ${fontSize}px sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(String(value), cx, cy + 1);
    }
    ctx.restore();
  }

  _drawBoard(board) {
    const size = CONFIG.BOARD_SIZE;
    const now = Date.now();
    const popCells = new Set();

    for (const anim of this.animations) {
      if (anim.type !== 'merge') continue;
      const t = Math.min(1, (now - anim.start) / anim.duration);
      if (t >= 1) continue;
      for (const [r, c] of anim.payload.cells || []) {
        popCells.add(`${r},${c}`);
      }
    }

    for (let r = 0; r < size; r++) {
      for (let c = 0; c < size; c++) {
        const v = board[r][c];
        let scale = 1;
        const key = `${r},${c}`;
        if (popCells.has(key)) {
          const anim = this.animations.find(
            (a) => a.type === 'merge' && (now - a.start) < a.duration
          );
          if (anim) {
            const t = (now - anim.start) / anim.duration;
            scale = 1 + 0.25 * Math.sin(t * Math.PI);
          }
        }
        this._drawCell(r, c, v, 1, scale);
      }
    }

    this.animations = this.animations.filter(
      (a) => now - a.start < a.duration
    );
  }

  _drawPreview(nextTile) {
    const ctx = this.ctx;
    const { previewY } = this.layout;
    ctx.fillStyle = CONFIG.TEXT_DIM;
    ctx.font = '16px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('下一个', this.w / 2, previewY);

    const size = 52;
    const x = this.w / 2 - size / 2;
    const y = previewY + 12;
    this._roundRect(x, y, size, size, 10);
    ctx.fillStyle = colorForValue(nextTile);
    ctx.fill();
    ctx.fillStyle = CONFIG.TEXT;
    ctx.font = 'bold 24px sans-serif';
    ctx.textBaseline = 'middle';
    ctx.fillText(String(nextTile), this.w / 2, y + size / 2 + 1);
  }

  _drawButton(rect, label, primary = false) {
    const ctx = this.ctx;
    this._roundRect(rect.x, rect.y, rect.w, rect.h, 8);
    ctx.fillStyle = primary ? '#6c5ce7' : 'rgba(255,255,255,0.12)';
    ctx.fill();
    ctx.fillStyle = CONFIG.TEXT;
    ctx.font = '16px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(label, rect.x + rect.w / 2, rect.y + rect.h / 2);
  }

  _drawFooter() {
    this._drawButton(this._restartBtn(), '重新开始');
    this._drawButton(this._shareBtn(), '分享');
  }

  _drawGameOver(score, maxVal) {
    const ctx = this.ctx;
    ctx.fillStyle = 'rgba(0,0,0,0.55)';
    ctx.fillRect(0, 0, this.w, this.h);

    ctx.fillStyle = CONFIG.TEXT;
    ctx.textAlign = 'center';
    ctx.font = 'bold 28px sans-serif';
    ctx.fillText('游戏结束', this.w / 2, this.h / 2 - 50);
    ctx.font = '20px sans-serif';
    ctx.fillStyle = CONFIG.TEXT_DIM;
    ctx.fillText(`本局得分：${score}`, this.w / 2, this.h / 2 - 10);
    ctx.fillText(`最大数字：${maxVal}`, this.w / 2, this.h / 2 + 24);

    this._drawButton(this._playAgainBtn(), '再来一局', true);
  }

  draw(state) {
    this._drawBg();
    this._drawHeader(state.score, state.best);
    this._drawBoard(state.board);
    this._drawPreview(state.nextTile);
    this._drawFooter();
    if (state.gameOver) {
      this._drawGameOver(state.score, state.maxValue);
    }
  }
}
