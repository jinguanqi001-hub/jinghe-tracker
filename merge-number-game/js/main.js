import { CONFIG, rollNextTile } from './config.js';
import { createBoard, isBoardFull, placeTile, maxOnBoard } from './board.js';
import { resolveMerges } from './merge.js';
import { loadBestScore, saveBestScore } from './storage.js';
import { Renderer } from './renderer.js';
import { Input } from './input.js';

class Game {
  constructor() {
    this.reset(false);
    this.best = loadBestScore();
    this._initCanvas();
    new Input(this.canvas, (x, y) => this.handleTap(x, y));
    this._loop();
  }

  _initCanvas() {
    let canvas;
    let ctx;
    let w;
    let h;

    if (typeof wx !== 'undefined' && wx.createCanvas) {
      canvas = wx.createCanvas();
      const sys = wx.getSystemInfoSync();
      w = sys.windowWidth;
      h = sys.windowHeight;
      const dpr = sys.pixelRatio || 1;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      ctx = canvas.getContext('2d');
      ctx.scale(dpr, dpr);
    } else if (typeof document !== 'undefined') {
      canvas = document.createElement('canvas');
      document.body.style.margin = '0';
      document.body.style.background = '#1a1a2e';
      document.body.appendChild(canvas);
      w = Math.min(420, window.innerWidth);
      h = Math.min(740, window.innerHeight);
      const dpr = window.devicePixelRatio || 1;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
      ctx = canvas.getContext('2d');
      ctx.scale(dpr, dpr);
    } else {
      throw new Error('No canvas environment');
    }

    this.canvas = canvas;
    this.ctx = ctx;
    this.screenW = w;
    this.screenH = h;
    this.renderer = new Renderer(canvas, ctx, w, h);
  }

  reset(persistBest = true) {
    this.board = createBoard();
    this.score = 0;
    this.nextTile = rollNextTile(this.best >= 50);
    this.gameOver = false;
    this.maxValue = 0;
    if (persistBest) this.best = loadBestScore();
    if (this.renderer) {
      this.renderer.setGameOver(false);
      this.renderer.animations = [];
    }
  }

  _share() {
    const title = `我在数字三合得了 ${this.score} 分，最大数字 ${this.maxValue}！`;
    if (typeof wx !== 'undefined' && wx.shareAppMessage) {
      wx.shareAppMessage({ title });
    } else {
      console.log('[分享]', title);
    }
  }

  handleTap(x, y) {
    if (this.renderer.hitPlayAgain(x, y) && this.gameOver) {
      this.reset();
      return;
    }
    if (this.renderer.hitRestart(x, y)) {
      this.reset();
      return;
    }
    if (this.renderer.hitShare(x, y)) {
      this._share();
      return;
    }
    if (this.gameOver) return;

    const cell = this.renderer.hitCell(x, y);
    if (!cell) return;

    const { r, c } = cell;
    if (!placeTile(this.board, r, c, this.nextTile)) return;

    const { board, mergeLog, totalScore } = resolveMerges(this.board);
    this.board = board;
    this.score += totalScore;

    for (const log of mergeLog) {
      for (const ev of log.events) {
        this.renderer.pushAnim('merge', ev);
      }
    }

    this.maxValue = maxOnBoard(this.board);
    if (this.score > this.best) {
      this.best = this.score;
      saveBestScore(this.best);
    }

    this.nextTile = rollNextTile(this.best >= 50);

    if (isBoardFull(this.board)) {
      this.gameOver = true;
      this.renderer.setGameOver(true);
    }
  }

  _loop() {
    const tick = () => {
      this.renderer.draw({
        board: this.board,
        score: this.score,
        best: this.best,
        nextTile: this.nextTile,
        gameOver: this.gameOver,
        maxValue: this.maxValue,
      });
      if (typeof requestAnimationFrame !== 'undefined') {
        requestAnimationFrame(tick);
      } else {
        setTimeout(tick, 16);
      }
    };
    tick();
  }
}

new Game();
