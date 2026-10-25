export class ClockMonitor {
  constructor({ toleranceMs = 120_000, onAnomaly }) {
    this.toleranceMs = toleranceMs;
    this.onAnomaly = onAnomaly;
    this.lastWall = Date.now();
    this.lastMono = performance.now();
    this.anomaly = false;
    this.highWaterMs = 0;
    this.lastElapsed = 0;
  }
  observe(run, wall = Date.now(), mono = performance.now()) {
    const expected = this.lastWall + (mono - this.lastMono);
    if (!this.anomaly && run && Math.abs(wall - expected) > this.toleranceMs) {
      this.anomaly = true;
      this.highWaterMs = Math.max(run.maxObservedElapsedMs || 0, this.lastElapsed, 0);
      this.onAnomaly?.(this.highWaterMs);
    }
    this.lastWall = wall;
    this.lastMono = mono;
    if (this.anomaly) return this.highWaterMs;
    this.lastElapsed = Math.max(this.lastElapsed, 0, run ? wall - run.startedAtMs : 0);
    return this.lastElapsed;
  }
  acceptRebased() { this.anomaly = false; this.lastElapsed = 0; this.lastWall = Date.now(); this.lastMono = performance.now(); }
}
