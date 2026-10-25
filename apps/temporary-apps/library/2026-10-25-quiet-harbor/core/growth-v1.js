import { RUN_YEAR } from "./time.js";

export const GROWTH_VERSION = 1;
export const MILESTONES = [
  { at: 0, count: 0, stage: "A seed finds the shore", label: "A quiet beginning" },
  { at: 10, count: 0, stage: "A small green shoot", label: "A little life is starting" },
  { at: 30, count: 0, stage: "Leaves unfold", label: "Your seedling is waking" },
  { at: 60, count: 0, stage: "A neighbor arrives", label: "Someone found the island" },
  { at: 180, count: 0, stage: "A path reaches the garden", label: "Room to grow" },
  { at: 300, count: 0, stage: "First garden beds", label: "A garden takes root" },
  { at: 900, count: 0, stage: "A cottage takes shape", label: "A home is on its way" },
  { at: 1800, count: 1, stage: "The first cottage", label: "A home by the shore" },
  { at: 3600, count: 2, stage: "A garden and a second home", label: "A neighborhood begins" },
  { at: 10800, count: 4, stage: "A close-knit cluster", label: "The village is growing" },
  { at: 21600, count: 7, stage: "A shared green", label: "A place to gather" },
  { at: 43200, count: 12, stage: "A little hamlet", label: "A handful of neighbors" },
  { at: 86400, count: 20, stage: "A village with a heart", label: "A village in bloom" },
  { at: 259200, count: 32, stage: "A market square", label: "A village taking shape" },
  { at: 604800, count: 48, stage: "A small coastal town", label: "A town by the water" },
  { at: 1209600, count: 72, stage: "A new neighborhood", label: "The town reaches outward" },
  { at: 2419200, count: 112, stage: "An established town", label: "A whole town is home" },
];

export function growthAt(elapsedMs) {
  const elapsed = Math.max(0, elapsedMs / 1000);
  let i = 0;
  while (i < MILESTONES.length - 1 && elapsed >= MILESTONES[i + 1].at) i++;
  const current = MILESTONES[i];
  const next = MILESTONES[i + 1];
  let completedBuildings = current.count;
  if (next && next.count > current.count) {
    const f = (elapsed - current.at) / (next.at - current.at);
    completedBuildings += Math.floor((next.count - current.count) * f);
  }
  const districts = elapsed < 2_419_200 ? 0 : Math.floor((elapsed - 2_419_200) / 604_800);
  if (districts) completedBuildings += districts * 16;
  const stages = ["seed", "sprout", "leaves", "person", "path", "garden", "home-foundation", "cottage", "neighborhood", "cluster", "green", "hamlet", "village", "market", "town", "district", "established"];
  const stageId = elapsed >= 2_419_200 ? "established" : stages[i];
  const bornAtSeconds = (index) => {
    let lo = 0, hi = 2_419_200;
    if (index >= 112) return 2_419_200 + (Math.floor((index - 112) / 16) + 1) * 604_800;
    for (let n = 0; n < 32; n++) {
      const mid = (lo + hi) / 2;
      const count = baseBuildingCount(mid);
      if (count >= index + 1) hi = mid; else lo = mid;
    }
    return hi;
  };
  return {
    elapsedSeconds: elapsed,
    stageId,
    stage: elapsed >= 2_419_200 ? `${districts} growing district${districts === 1 ? "" : "s"}` : current.stage,
    label: current.label,
    completedBuildings,
    districts,
    personPresent: elapsed >= 60,
    pathPresent: elapsed >= 180,
    gardenPresent: elapsed >= 300,
    foundationPresent: elapsed >= 900 && elapsed < 1800,
    firstSprout: elapsed >= 10,
    fullLeaves: elapsed >= 30,
    bornAtSeconds,
    seasonalPhase: (elapsed % RUN_YEAR) / RUN_YEAR,
  };
}

function baseBuildingCount(seconds) {
  let i = 0;
  while (i < MILESTONES.length - 1 && seconds >= MILESTONES[i + 1].at) i++;
  const a = MILESTONES[i], b = MILESTONES[i + 1];
  if (!b) return a.count;
  return a.count + Math.floor(Math.max(0, b.count - a.count) * ((seconds - a.at) / (b.at - a.at)));
}
