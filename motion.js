// Effects stay optional: no motion for touch pointers or reduced-motion users.
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
const finePointer = matchMedia('(hover: hover) and (pointer: fine)');
const effects = new WeakMap();
const activeEffects = new Set();
function animate(element, frames, options) {
  effects.get(element)?.cancel();
  const effect = element.animate(frames, options);
  effects.set(element, effect);
  activeEffects.add(effect);
  const cleanup = () => {
    activeEffects.delete(effect);
    if (effects.get(element) === effect) effects.delete(element);
  };
  effect.onfinish = cleanup;
  effect.oncancel = cleanup;
}
export function fadeIn(element) {
  if (reducedMotion.matches) return;
  animate(element, [
    { opacity: 0, transform: 'translateY(7px)' },
    { opacity: 1, transform: 'translateY(0)' }
  ], { duration: 240, easing: 'cubic-bezier(.2,.7,.2,1)' });
}
export function initMotion() {
  let magnet = null;
  let bounds = null;
  let frame = null;
  let position = null;
  function reset() {
    if (frame !== null) cancelAnimationFrame(frame);
    frame = null;
    if (magnet) {
      magnet.classList.remove('magnetic-hover');
      for (const key of ['--magnet-x', '--magnet-y', '--magnet-stretch']) magnet.style.removeProperty(key);
    }
    magnet = null; bounds = null;
  }
  document.addEventListener('pointermove', event => {
    if (reducedMotion.matches || !finePointer.matches || event.pointerType !== 'mouse') return;
    const button = event.target.closest('button:not(:disabled)');
    if (!button) { reset(); return; }
    if (button !== magnet) {
      reset(); magnet = button; bounds = button.getBoundingClientRect();
      button.classList.add('magnetic-hover');
    }
    position = { x: event.clientX, y: event.clientY };
    if (frame !== null) return;
    frame = requestAnimationFrame(() => {
      frame = null;
      if (!magnet?.isConnected || !bounds) { reset(); return; }
      const x = Math.max(-1, Math.min(1, (position.x - bounds.left - bounds.width / 2) / (bounds.width / 2)));
      const y = Math.max(-1, Math.min(1, (position.y - bounds.top - bounds.height / 2) / (bounds.height / 2)));
      magnet.style.setProperty('--magnet-x', `${x * 5}px`);
      magnet.style.setProperty('--magnet-y', `${y * 3}px`);
      magnet.style.setProperty('--magnet-stretch', String(1 + Math.abs(x) * .025));
    });
  });
  document.addEventListener('pointerout', event => {
    if (magnet && !magnet.contains(event.relatedTarget)) reset();
  });
  document.addEventListener('pointercancel', reset);
  document.addEventListener('scroll', reset, true);
  window.addEventListener('blur', reset);
  window.addEventListener('resize', reset);
  document.addEventListener('click', event => {
    const button = event.target.closest('button:not(:disabled)');
    if (!button || reducedMotion.matches) return;
    animate(button, [{ opacity: 1 }, { opacity: .55, offset: .3 }, { opacity: 1 }], { duration: 260, easing: 'ease-out' });
  }, true);
  reducedMotion.addEventListener('change', () => {
    reset();
    if (reducedMotion.matches) for (const effect of activeEffects) effect.cancel();
  });
  finePointer.addEventListener('change', reset);
}
