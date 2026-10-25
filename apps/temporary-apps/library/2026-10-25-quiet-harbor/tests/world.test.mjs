import test from "node:test";
import assert from "node:assert/strict";
import { growthAt } from "../core/growth-v1.js";
import { buildingLot, districtChunk, worldFor } from "../core/world-v1.js";

test("first seed, neighbor, garden, house and district milestones are stable", () => {
  assert.equal(growthAt(0).completedBuildings, 0);
  assert.equal(growthAt(60_000).personPresent, true);
  assert.equal(growthAt(1_800_000).completedBuildings, 1);
  assert.equal(growthAt(2_419_200_000).completedBuildings, 112);
  assert.equal(growthAt(3_024_000_000).districts, 1);
  assert.equal(growthAt(3_024_000_000).completedBuildings, 128);
});

test("growing world is seeded, locally clustered, and expands districts", () => {
  assert.deepEqual(buildingLot("abc", 35), buildingLot("abc", 35));
  assert.notDeepEqual(buildingLot("abc", 35), buildingLot("def", 35));
  assert.deepEqual(districtChunk(0), districtChunk(0));
  const early = worldFor("abc", 3_600_000);
  const later = worldFor("abc", 86_400_000);
  assert.ok(later.buildings.length > early.buildings.length);
  assert.ok(later.terrainRadius > early.terrainRadius);
  assert.equal(later.residents.length, Math.min(10, Math.floor(1 + later.growth.completedBuildings / 7)));
  assert.ok(later.buildings.every((home) => home.startsAtSeconds <= home.birthAtSeconds));
});

test("the first cottage begins construction before the half-hour milestone", () => {
  assert.equal(worldFor("abc", 1_680_000).buildings.at(-1).id, "home-0");
  assert.ok(worldFor("abc", 1_680_000).buildings.at(-1).startsAtSeconds < 1_800);
});
