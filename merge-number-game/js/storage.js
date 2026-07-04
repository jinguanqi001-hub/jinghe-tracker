const KEY = 'merge_number_best';

export function loadBestScore() {
  try {
    if (typeof wx !== 'undefined' && wx.getStorageSync) {
      return wx.getStorageSync(KEY) || 0;
    }
    if (typeof localStorage !== 'undefined') {
      return parseInt(localStorage.getItem(KEY), 10) || 0;
    }
  } catch (e) {
    /* ignore */
  }
  return 0;
}

export function saveBestScore(score) {
  try {
    if (typeof wx !== 'undefined' && wx.setStorageSync) {
      wx.setStorageSync(KEY, score);
      return;
    }
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(KEY, String(score));
    }
  } catch (e) {
    /* ignore */
  }
}
