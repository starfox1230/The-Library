import test from "node:test";
import assert from "node:assert/strict";
import { BUILDING_TYPES, FIRST_LANDMARKS, buildingTypeFor, buildingDefinition, townCounts } from "../core/building-types.js";
import { growthAt } from "../core/growth-v1.js";
import { buildingLot, worldFor } from "../core/world-v1.js";

test("landmarks arrive gradually without replacing the first cottages", () => {
  assert.deepEqual(worldFor("harbor", 3_600_000).buildings.map(({ type }) => type), ["cottage", "cottage"]);
  const born = growthAt(0).bornAtSeconds;
  assert.ok(Math.abs(born(19) - 86_400) < .001);
  assert.ok(Math.abs(born(25) - 172_800) < .001);
  assert.ok(Math.abs(born(55) - 806_400) < .001);
  for (const { slot, type } of FIRST_LANDMARKS) {
    const ready = worldFor("harbor", born(slot) * 1000 + 1);
    assert.equal(ready.buildings[slot].type, type);
    assert.ok(ready.growth.completedBuildings > slot);
    const before = worldFor("harbor", (born(slot) - 121) * 1000);
    assert.ok(!before.buildings.some((building) => building.type === type));
  }
});

test("the expansion preserves existing run coordinates, lot IDs, variants and construction ages", () => {
  const expected = [
    { id: "home-0", x: 0, y: 0, kind: "home", variant: 4 },
    { id: "home-19", x: -5, y: -2, kind: "civic", variant: 7 },
    { id: "home-35", x: -5, y: 10, kind: "civic", variant: 4 },
    { id: "home-111", x: -12, y: -14, kind: "home", variant: 1 },
    { id: "district-0-lot-0", x: 35, y: -14, kind: "home", variant: 5 },
    { id: "district-0-lot-5", x: 38, y: -11, kind: "civic", variant: 0 },
    { id: "district-1-lot-15", x: 43, y: 12, kind: "home", variant: 3 },
  ];
  const slots = [0, 19, 35, 111, 112, 117, 143];
  const world = worldFor("harbor", 100 * 86_400_000);
  for (let i = 0; i < slots.length; i++) {
    const slot = slots[i];
    assert.deepEqual(buildingLot("harbor", slot), expected[i]);
    const { type, birthAtSeconds, startsAtSeconds, buildSeconds, ...lot } = world.buildings[slot];
    assert.deepEqual(lot, expected[i]);
    assert.equal(birthAtSeconds, world.growth.bornAtSeconds(slot));
    assert.equal(startsAtSeconds + buildSeconds, birthAtSeconds);
    assert.ok(BUILDING_TYPES[type]);
  }
});

test("future districts have a reproducible mix of homes, shops and distinct community places", () => {
  const seen = new Set();
  for (let district = 0; district < 30; district++) {
    const types = Array.from({ length: 16 }, (_, lot) => buildingTypeFor("harbor", 112 + district * 16 + lot));
    assert.equal(types.filter((type) => type === "cottage").length, 12);
    assert.notEqual(types[5], types[12]);
    for (const type of types) { assert.ok(BUILDING_TYPES[type]); seen.add(type); }
    assert.deepEqual(types, Array.from({ length: 16 }, (_, lot) => buildingTypeFor("harbor", 112 + district * 16 + lot)));
  }
  assert.deepEqual([...seen].sort(), Object.keys(BUILDING_TYPES).sort());
  assert.notDeepEqual(Array.from({ length: 32 }, (_, i) => buildingTypeFor("harbor", 112 + i)), Array.from({ length: 32 }, (_, i) => buildingTypeFor("different-run", 112 + i)));
});

test("the summary counts actual homes separately and titles explain each public place", () => {
  assert.deepEqual(townCounts("harbor", 26), { homes: 21, places: 5 });
  for (const type of Object.keys(BUILDING_TYPES)) {
    const info = buildingDefinition({ type, kind: "home" });
    assert.ok(info.name.length > 3 && info.description.length > 20);
  }
  assert.equal(buildingDefinition({ kind: "civic" }).name, "Town hall");
});
