const HOLD_MS = 1000;
const EDGE_SLOP_PX = 12;

export class HoldController {
  constructor(button, { onProgress, onComplete }) {
    this.button = button;
    this.onProgress = onProgress;
    this.onComplete = onComplete;
    this.active = false;
    this.completed = false;
    this.pointerId = null;
    this.startedAt = 0;
    this.frameId = 0;
    this.key = null;
    this.onPointerDown = (event) => this.pointerDown(event);
    this.onPointerUp = (event) => this.pointerUp(event);
    this.onPointerCancel = () => this.cancel();
    this.onClick = (event) => this.click(event);
    this.onKeyDown = (event) => this.keyDown(event);
    this.onKeyUp = (event) => this.keyUp(event);
    this.button.addEventListener("pointerdown", this.onPointerDown);
    this.button.addEventListener("pointerup", this.onPointerUp);
    this.button.addEventListener("pointercancel", this.onPointerCancel);
    this.button.addEventListener("lostpointercapture", this.onPointerCancel);
    this.button.addEventListener("click", this.onClick);
    this.button.addEventListener("keydown", this.onKeyDown);
    this.button.addEventListener("keyup", this.onKeyUp);
    this.onVisibility = () => { if (document.hidden) this.cancel(); };
    this.onBlur = () => this.cancel();
    document.addEventListener("visibilitychange", this.onVisibility);
    window.addEventListener("blur", this.onBlur);
  }

  pointerDown(event) {
    if (!this.active || this.completed) return;
    if (event.button !== undefined && event.button !== 0) return;
    if (this.pointerId !== null || this.key) { this.cancel(); return; }
    event.preventDefault();
    this.pointerId = event.pointerId;
    try { this.button.setPointerCapture(event.pointerId); } catch { /* capture may already be lost */ }
    this.start();
  }

  pointerUp(event) {
    if (this.pointerId !== event.pointerId) return;
    const elapsed = performance.now() - this.startedAt;
    const rect = this.button.getBoundingClientRect();
    const inside = event.clientX >= rect.left - EDGE_SLOP_PX && event.clientX <= rect.right + EDGE_SLOP_PX && event.clientY >= rect.top - EDGE_SLOP_PX && event.clientY <= rect.bottom + EDGE_SLOP_PX;
    this.pointerId = null;
    this.stopFrame();
    if (elapsed >= HOLD_MS && inside) this.finish(); else this.cancel();
    this.swallowClick = true;
  }

  click(event) {
    if (event.detail === 0 && this.swallowClick) { this.swallowClick = false; event.preventDefault(); event.stopImmediatePropagation(); return; }
    if (event.detail !== 0) {
      if (this.swallowClick) { this.swallowClick = false; event.preventDefault(); event.stopImmediatePropagation(); }
      return;
    }
    if (this.active) {
      event.preventDefault();
      this.cancel();
      this.onAccessibleActivation?.();
    } else {
      event.preventDefault();
      this.onAccessibleActivation?.();
    }
  }

  keyDown(event) {
    if (!this.active || this.completed || event.repeat || ![" ", "Enter"].includes(event.key) || this.key) return;
    event.preventDefault();
    this.key = event.key;
    this.start();
  }

  keyUp(event) {
    if (!this.key || event.key !== this.key) return;
    event.preventDefault();
    const done = performance.now() - this.startedAt >= HOLD_MS;
    this.key = null;
    this.stopFrame();
    if (done) this.finish(); else this.cancel();
  }

  start() {
    this.startedAt = performance.now();
    this.onProgress(0);
    const tick = () => {
      if (this.pointerId === null && this.key === null) return;
      const progress = Math.min(1, (performance.now() - this.startedAt) / HOLD_MS);
      this.onProgress(progress);
      if (progress >= 1) this.finish(); else this.frameId = requestAnimationFrame(tick);
    };
    this.frameId = requestAnimationFrame(tick);
  }

  finish() {
    if (this.completed) return;
    this.completed = true;
    this.pointerId = null;
    this.key = null;
    this.stopFrame();
    this.onProgress(1);
    this.swallowClick = true;
    this.onComplete();
    this.completed = false;
  }

  cancel() {
    if (this.frameId) this.stopFrame();
    this.pointerId = null;
    this.key = null;
    this.onProgress(0);
  }

  stopFrame() {
    if (this.frameId) cancelAnimationFrame(this.frameId);
    this.frameId = 0;
  }

  setEnabled(enabled) {
    this.active = enabled;
    if (!enabled) this.cancel();
    this.button.setAttribute("aria-label", enabled ? "I picked — hold for one second to begin again" : "Begin growing your island");
  }

  destroy() {
    this.cancel();
    this.button.removeEventListener("pointerdown", this.onPointerDown);
    this.button.removeEventListener("pointerup", this.onPointerUp);
    this.button.removeEventListener("pointercancel", this.onPointerCancel);
    this.button.removeEventListener("lostpointercapture", this.onPointerCancel);
    this.button.removeEventListener("click", this.onClick);
    this.button.removeEventListener("keydown", this.onKeyDown);
    this.button.removeEventListener("keyup", this.onKeyUp);
    document.removeEventListener("visibilitychange", this.onVisibility);
    window.removeEventListener("blur", this.onBlur);
  }
}
