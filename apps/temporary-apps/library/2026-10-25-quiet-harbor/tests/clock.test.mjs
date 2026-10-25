import test from "node:test";
import assert from "node:assert/strict";
import { ClockMonitor } from "../core/clock.js";

test("resuming after a device sleep counts wall time without reporting a clock change", () => {
  const anomalies = [];
  const monitor = new ClockMonitor({ onAnomaly: (elapsed) => anomalies.push(elapsed) });
  const run = { startedAtMs: 1_000, maxObservedElapsedMs: 0 };

  monitor.resume(1_000, 10_000);
  assert.equal(monitor.observe(run, 1_000, 10_000), 0);
  monitor.resume(601_000, 10_000); // wall clock advanced while the monotonic clock paused

  assert.equal(monitor.observe(run, 601_000, 10_000), 600_000);
  assert.deepEqual(anomalies, []);
});

test("resume clears a sleep-related anomaly observed just before the app became visible", () => {
  const anomalies = [];
  const monitor = new ClockMonitor({ onAnomaly: (elapsed) => anomalies.push(elapsed) });
  const run = { startedAtMs: 1_000, maxObservedElapsedMs: 0 };

  monitor.resume(1_000, 10_000);
  assert.equal(monitor.observe(run, 1_000, 10_000), 0);
  assert.equal(monitor.observe(run, 601_000, 10_000), 0);
  assert.deepEqual(anomalies, [0]);

  assert.equal(monitor.resume(601_000, 10_000), true);
  assert.equal(monitor.observe(run, 601_000, 10_000), 600_000);
  assert.deepEqual(anomalies, [0]);
});

test("a wall-clock jump while the app remains active still reports an anomaly", () => {
  const anomalies = [];
  const monitor = new ClockMonitor({ onAnomaly: (elapsed) => anomalies.push(elapsed) });
  const run = { startedAtMs: 1_000, maxObservedElapsedMs: 0 };

  monitor.resume(1_000, 10_000);
  monitor.observe(run, 1_000, 10_000);
  monitor.observe(run, 601_000, 10_000);

  assert.deepEqual(anomalies, [0]);
});
