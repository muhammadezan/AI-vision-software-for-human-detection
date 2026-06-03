(function () {
  'use strict';

  const POLL_MS = 80;
  let activeBtn    = null;
  let lastProgress = 0;
  let lastBlink    = false;

  function injectStyles() {
    if (document.getElementById('__dwell_style')) return;
    const s = document.createElement('style');
    s.id = '__dwell_style';
    s.textContent = `
      .__dwell_bar {
        position: absolute;
        bottom: 0; left: 0;
        height: 4px; width: 0%;
        background: #00e5ff;
        border-radius: 2px;
        transition: width 0.08s linear;
        pointer-events: none;
        z-index: 999;
      }
      .blink-flash {
        outline: 3px solid #00e5ff !important;
        transition: outline 0.3s ease-out;
      }
    `;
    document.head.appendChild(s);
  }

  function tagButtons() {
    const sel = [
      'button', '[role="button"]', '.btn',
      '.symbol-btn', '.word-btn', '.letter-btn',
      '.phrase-btn', '.nav-btn', '.key'
    ].join(',');
    document.querySelectorAll(sel).forEach(el => {
      if (!el.getAttribute('data-dwell-btn')) {
        el.setAttribute('data-dwell-btn', '1');
        el.style.position = 'relative';
        el.style.overflow = 'hidden';
      }
    });
  }

  function getOrCreateBar(btn) {
    let bar = btn.querySelector('.__dwell_bar');
    if (!bar) {
      bar = document.createElement('div');
      bar.className = '__dwell_bar';
      btn.appendChild(bar);
    }
    return bar;
  }

  function setProgress(btn, progress) {
    const bar = getOrCreateBar(btn);
    bar.style.width = (progress * 100).toFixed(1) + '%';
    bar.style.background = progress >= 1.0 ? '#00ff88' : '#00e5ff';
  }

  function clearProgress(btn) {
    if (!btn) return;
    const bar = btn.querySelector('.__dwell_bar');
    if (bar) bar.style.width = '0%';
  }

  function getButtonUnderGaze() {
    const x = window._gazeX || window.innerWidth / 2;
    const y = window._gazeY || window.innerHeight / 2;
    const el = document.elementFromPoint(x, y);
    if (!el) return null;
    return el.closest('[data-dwell-btn]') || null;
  }

  async function poll() {
    try {
      const res  = await fetch('/api/gaze/current');
      const data = await res.json();

      if (data.gaze_normalized) {
        window._gazeX = data.gaze_normalized.x * window.innerWidth;
        window._gazeY = data.gaze_normalized.y * window.innerHeight;
      }

      const progress  = data.dwell_progress || 0;
      const blinkNow  = data.blink_detected  || false;
      const hoveredBtn = getButtonUnderGaze();

      // Switched button — clear old bar
      if (hoveredBtn !== activeBtn) {
        clearProgress(activeBtn);
        activeBtn = hoveredBtn;
      }

      if (activeBtn) {
        setProgress(activeBtn, progress);
        // Dwell complete
        if (progress >= 1.0 && lastProgress < 1.0) {
          activeBtn.click();
          console.log('DWELL CLICK:', activeBtn.textContent.trim());
        }
      }

      // Blink click — only on fresh blink (edge detection)
      if (blinkNow && !lastBlink) {
        const target = hoveredBtn ||
          document.elementFromPoint(window._gazeX, window._gazeY);
        if (target) {
          target.click();
          target.classList.add('blink-flash');
          setTimeout(() => target.classList.remove('blink-flash'), 400);
          console.log('BLINK CLICK:', target.textContent?.trim());
        }
      }

      lastProgress = progress;
      lastBlink    = blinkNow;

    } catch (e) {
      // server not ready — ignore silently
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    injectStyles();
    tagButtons();
    setInterval(poll, POLL_MS);
    // Re-tag dynamic buttons
    new MutationObserver(tagButtons)
      .observe(document.body, { childList: true, subtree: true });
  });

})();