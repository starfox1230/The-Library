import { randomFor, hash32 } from "./random-v1.js";
import { growthAt } from "./growth-v1.js";

export const GENERATOR_VERSION = 1;
const CORE_HOUSE_SLOTS = 112;
const CELL = 3;

function squareSpiral(index) {
  if (index === 0) return [0, 0];
  const ring = Math.ceil((Math.sqrt(index + 1) - 1) / 2);
  const side = ring * 2;
  const max = (ring * 2 + 1) ** 2 - 1;
  const d = max - index;
  if (d < side) return [ring - d, -ring];
  if (d < side * 2) return [-ring, -ring + (d - side)];
  if (d < side * 3) return [-ring + (d - side * 2), ring];
  return [ring, ring - (d - side * 3)];
}

export function buildingLot(seed, id) {
  if (id < CORE_HOUSE_SLOTS) {
    const [sx, sy] = squareSpiral(id);
    const rand = randomFor(seed, `lot:${id}`);
    return { id: `home-${id}`, x: sx * CELL + Math.floor(rand() * 2), y: sy * CELL + Math.floor(rand() * 2), kind: id === 19 || id === 35 ? "civic" : "home", variant: Math.floor(rand() * 8) };
  }
  const districtIndex = Math.floor((id - CORE_HOUSE_SLOTS) / 16);
  const lotIndex = (id - CORE_HOUSE_SLOTS) % 16;
  const [cx, cy] = districtChunk(districtIndex);
  const rand = randomFor(seed, `district:${districtIndex}:lot:${lotIndex}`);
  return { id: `district-${districtIndex}-lot-${lotIndex}`, x: cx * 16 + 2 + (lotIndex % 4) * 3 + Math.floor(rand() * 2), y: cy * 16 + 2 + Math.floor(lotIndex / 4) * 3 + Math.floor(rand() * 2), kind: lotIndex === 5 ? "civic" : "home", variant: Math.floor(rand() * 8) };
}

export function districtChunk(index) {
  return squareSpiral(index + 9); // the surrounding ring follows the reserved 3×3 core
}

export function terrainAt(seed, gx, gy, elapsedMs) {
  const days = Math.max(0, elapsedMs / 86_400_000);
  const radius = 4 + Math.sqrt(days) * 5.9;
  const jitter = (hash32(`${Math.floor(gx / 3)},${Math.floor(gy / 3)}`, hash32(seed)) % 1000) / 1000;
  const dist = Math.hypot(gx / 1.13, gy);
  if (dist > radius + jitter * 1.5) return null;
  const surface = ["landscapeTiles_010", "landscapeTiles_015", "landscapeTiles_016", "landscapeTiles_022", "landscapeTiles_067", "landscapeTiles_075"];
  const rand = randomFor(seed, `terrain:${gx}:${gy}`);
  return { kind: "ground", gx, gy, tile: surface[Math.floor(rand() * surface.length)] };
}

export function worldFor(seed, elapsedMs) {
  const age = Math.max(0, elapsedMs);
  const growth = growthAt(age);
  let visibleBuildingCount = growth.completedBuildings;
  const nextBirth = growth.bornAtSeconds(growth.completedBuildings);
  const nextGap = growth.completedBuildings ? Math.max(0, nextBirth - growth.bornAtSeconds(growth.completedBuildings - 1)) : 900;
  if (age / 1000 + 0.01 >= nextBirth - Math.min(120, Math.max(10, 0.25 * nextGap))) visibleBuildingCount++;
  const buildings = Array.from({ length: visibleBuildingCount }, (_, i) => {
    const lot = buildingLot(seed, i);
    const birthAtSeconds = growth.bornAtSeconds(i);
    const previousBirth = i ? growth.bornAtSeconds(i - 1) : 900;
    const gap = i ? Math.max(0, birthAtSeconds - previousBirth) : 900;
    const buildSeconds = Math.min(120, Math.max(10, 0.25 * gap));
    return { ...lot, birthAtSeconds, startsAtSeconds: birthAtSeconds - buildSeconds, buildSeconds };
  });
  const present = growth.personPresent;
  const home = buildings.slice(-1)[0];
  return {
    seed,
    growth,
    buildings,
    terrainRadius: 4 + Math.sqrt(age / 86_400_000) * 5.9,
    residents: present ? makeResidents(seed, age, Math.min(10, 1 + growth.completedBuildings / 7), home) : [],
    gardenFlowers: growth.gardenPresent ? 3 + (hash32(`${seed}:garden`) % 6) : 0,
  };
}

export function makeResidents(seed, elapsedMs, count, destination) {
  const time = elapsedMs / 1000;
  return Array.from({ length: Math.min(10, count) }, (_, id) => {
    const rand = randomFor(seed, `resident:${id}`);
    const phase = rand() * Math.PI * 2;
    const radius = 1 + rand() * 4.2;
    const speed = 0.08 + rand() * 0.12;
    const walking = time * speed + phase;
    return { id, x: destination ? destination.x + Math.cos(walking) * radius : Math.cos(walking) * radius, y: destination ? destination.y + Math.sin(walking * 0.7) * radius : Math.sin(walking * 0.7) * radius, phase: walking };
  });
}
