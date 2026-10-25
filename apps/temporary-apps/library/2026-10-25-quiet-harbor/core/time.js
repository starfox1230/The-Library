const SECOND = 1_000;
export const RUN_YEAR = 365 * 24 * 60 * 60 * SECOND;

/** @param {number} elapsedMs */
export function splitDuration(elapsedMs) {
  let n = Math.floor(Math.max(0, Number.isFinite(elapsedMs) ? elapsedMs : 0) / SECOND);
  const years = Math.floor(n / 31_536_000);
  n %= 31_536_000;
  const weeks = Math.floor(n / 604_800);
  n %= 604_800;
  const days = Math.floor(n / 86_400);
  n %= 86_400;
  const hours = Math.floor(n / 3_600);
  n %= 3_600;
  const minutes = Math.floor(n / 60);
  const seconds = n % 60;
  return { years, weeks, days, hours, minutes, seconds, totalSeconds: Math.floor(Math.max(0, Number.isFinite(elapsedMs) ? elapsedMs : 0) / SECOND) };
}

/** A fixed-unit display; years are 365 days and months are deliberately omitted. */
export function formatDuration(elapsedMs) {
  const d = splitDuration(elapsedMs);
  const pad = (n) => String(n).padStart(2, "0");
  const parts = [];
  if (d.years) parts.push(`${d.years}y`);
  if (d.weeks || d.years) parts.push(`${d.years ? d.weeks : d.weeks}w`);
  if (d.days || d.weeks || d.years) parts.push(`${d.days}d`);
  if (d.hours || d.days || d.weeks || d.years) parts.push(`${pad(d.hours)}h`);
  if (d.minutes || d.hours || d.days || d.weeks || d.years) parts.push(`${pad(d.minutes)}m`);
  parts.push(`${pad(d.seconds)}s`);
  return parts.join(" ");
}

export function longDurationLabel(elapsedMs) {
  const d = splitDuration(elapsedMs);
  const units = [[d.years, "year"], [d.weeks, "week"], [d.days, "day"], [d.hours, "hour"], [d.minutes, "minute"], [d.seconds, "second"]];
  return units.map(([value, unit]) => `${value} ${unit}${value === 1 ? "" : "s"}`).join(", ");
}

export function elapsedForRun(run, nowMs = Date.now()) {
  if (!run || !Number.isFinite(run.startedAtMs)) return 0;
  const end = Number.isFinite(run.endedAtMs) ? run.endedAtMs : nowMs;
  return Math.max(0, Number.isFinite(run.elapsedAtEndMs) ? run.elapsedAtEndMs : end - run.startedAtMs);
}
