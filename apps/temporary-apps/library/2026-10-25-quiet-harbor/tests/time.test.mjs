import test from "node:test";
import assert from "node:assert/strict";
import { formatDuration, splitDuration, elapsedForRun } from "../core/time.js";

test("timer always shows seconds and adds larger fixed units", () => {
  assert.equal(formatDuration(0), "00s");
  assert.equal(formatDuration(59_999), "59s");
  assert.equal(formatDuration(60_000), "01m 00s");
  assert.equal(formatDuration(3_600_000), "01h 00m 00s");
  assert.equal(formatDuration(86_400_000), "1d 00h 00m 00s");
  assert.equal(formatDuration(604_800_000), "1w 0d 00h 00m 00s");
  assert.equal(formatDuration(31_536_000_000), "1y 0w 0d 00h 00m 00s");
});

test("duration components normalize without losing seconds", () => {
  assert.deepEqual(splitDuration(90061_000), { years: 0, weeks: 0, days: 1, hours: 1, minutes: 1, seconds: 1, totalSeconds: 90061 });
  assert.equal(splitDuration(-1).totalSeconds, 0);
});

test("ended run uses its saved duration rather than the current wall clock", () => {
  assert.equal(elapsedForRun({ startedAtMs: 100, endedAtMs: 9_100, elapsedAtEndMs: 9_000 }, 50_000), 9_000);
});
