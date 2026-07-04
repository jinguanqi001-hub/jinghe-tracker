/** 统一触摸/鼠标输入 */
export class Input {
  constructor(canvas, onTap) {
    this.onTap = onTap;
    this._bind(canvas);
  }

  _bind(canvas) {
    const handler = (e) => {
      const touch = e.touches ? e.touches[0] : e;
      const x = touch.clientX;
      const y = touch.clientY;
      this.onTap(x, y);
    };

    if (typeof wx !== 'undefined') {
      wx.onTouchStart((e) => {
        if (!e.touches || !e.touches.length) return;
        const t = e.touches[0];
        this.onTap(t.clientX, t.clientY);
      });
    } else if (canvas && canvas.addEventListener) {
      canvas.addEventListener('touchstart', (e) => {
        e.preventDefault();
        handler(e);
      });
      canvas.addEventListener('mousedown', handler);
    }
  }
}
