import { splitDuration } from "./time.js";

/** Calendar units and clock digits use separate rows, with seconds always visible. */
export function displayDuration(elapsedMs) {
  const d = splitDuration(elapsedMs);
  const calendar = d.years ? ["years", "weeks", "days"] : d.weeks ? ["weeks", "days"] : d.days ? ["days"] : [];
  const clock = calendar.length || d.hours ? ["hours", "minutes", "seconds"] : d.minutes ? ["minutes", "seconds"] : ["seconds"];
  return {
    calendar: calendar.map((unit) => ({ unit, value: String(d[unit]) })),
    clock: clock.map((unit) => ({ unit, value: String(d[unit]).padStart(2, "0") })),
  };
}
