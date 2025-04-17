/**
 * Simple Scroll Position Fix for docs.neuroca.dev
 * 
 * This script fixes the issue where the page jumps back to the top when scrolling.
 * It uses a minimal, elegant approach that disables native scroll restoration
 * and watches for unexpected scroll position changes.
 */

;(function() {
  // 1) Turn off native scroll restoration (so browser won't override us)
  if ('scrollRestoration' in history) {
    history.scrollRestoration = 'manual';
  }

  let lastY = 0;
  let isRestoring = false;

  // 2) Track user scroll
  window.addEventListener('scroll', () => {
    if (!isRestoring) lastY = window.scrollY;
  }, { passive: true });

  // 3) When the page "settles" (e.g. on load), jump back if we've been yanked
  window.addEventListener('load', () => {
    if (Math.abs(window.scrollY - lastY) > 10) {
      window.scrollTo(0, lastY);
    }
  });

  // 4) Watch for DOM mutations (e.g. Mermaid/MathJax rendering) that may shift layout
  new MutationObserver(() => {
    if (Math.abs(window.scrollY - lastY) > 50) {
      isRestoring = true;
      window.scrollTo(0, lastY);
      // unlock after a tick so user can scroll again
      setTimeout(() => { isRestoring = false; }, 100);
    }
  }).observe(document.documentElement, {
    childList: true,
    subtree: true,
    attributes: true
  });
})();
