import { hash32 } from "./random-v1.js";

// Presentation expands the existing lots without changing their coordinates,
// IDs, construction times, run seeds, or the saved generator version.
export const BUILDING_TYPES = Object.freeze({
  cottage: { name: "Coastal cottage", category: "home", description: "A warm little home, with a garden at the doorstep." },
  bakery: { name: "Village bakery", category: "shop", description: "Fresh bread, a striped awning, and a place to start the morning." },
  cafe: { name: "Corner café", category: "shop", description: "A little coffee shop with a sunny outdoor table." },
  market: { name: "Neighborhood market", category: "shop", description: "Colorful stalls bring neighbors and their harvests together." },
  school: { name: "Village school", category: "community", description: "A schoolhouse with a bell tower, flag, and room for curious minds." },
  "fire-station": { name: "Fire station", category: "community", description: "Red garage doors, a lookout tower, and a little fire engine ready to help." },
  park: { name: "Fountain garden", category: "green", description: "A leafy public garden with a fountain and benches for a quiet moment." },
  library: { name: "Public library", category: "community", description: "Tall windows and shelves of stories give the town a place to read." },
  clinic: { name: "Community clinic", category: "community", description: "A bright neighborhood clinic, marked by a green cross." },
  museum: { name: "Town museum", category: "community", description: "A columned museum with a classical pediment and discoveries inside." },
  "town-hall": { name: "Town hall", category: "community", description: "A clock tower marks the heart of the growing community." },
  greenhouse: { name: "Glasshouse", category: "green", description: "A glass-roofed greenhouse shelters rows of greenery through the seasons." },
  observatory: { name: "Town observatory", category: "community", description: "A blue dome and a little telescope turn the town's eyes toward the stars." },
  theater: { name: "Community theater", category: "community", description: "A lit marquee and velvet-red entrance welcome the town for a show." },
});

export const FIRST_LANDMARKS = Object.freeze([
  { slot: 6, type: "bakery" },
  { slot: 9, type: "cafe" },
  { slot: 13, type: "market" },
  { slot: 19, type: "school" },
  { slot: 25, type: "fire-station" },
  { slot: 30, type: "park" },
  { slot: 35, type: "library" },
  { slot: 43, type: "clinic" },
  { slot: 55, type: "museum" },
  { slot: 71, type: "town-hall" },
  { slot: 87, type: "greenhouse" },
  { slot: 103, type: "observatory" },
  { slot: 111, type: "theater" },
]);
const CORE_TYPES = new Map(FIRST_LANDMARKS.map(({ slot, type }) => [slot, type]));
const COMMUNITY = ["school", "fire-station", "library", "clinic", "museum", "town-hall", "greenhouse", "observatory", "theater"];
const SHOPS = ["bakery", "cafe", "market"];

export function buildingTypeFor(seed, slot) {
  if (slot < 112) return CORE_TYPES.get(slot) || "cottage";
  const district = Math.floor((slot - 112) / 16);
  const lot = (slot - 112) % 16;
  const rotation = hash32(`${seed}:town-life`);
  if (lot === 2) return SHOPS[(rotation + district) % SHOPS.length];
  if (lot === 5 || lot === 12) return COMMUNITY[(rotation + district + (lot === 12 ? 4 : 0)) % COMMUNITY.length];
  if (lot === 14) return "park";
  return "cottage";
}

export function buildingDefinition(building) {
  return BUILDING_TYPES[building.type] || BUILDING_TYPES[building.kind === "civic" ? "town-hall" : "cottage"];
}

export function townCounts(seed, completedBuildings) {
  let homes = 0;
  for (let slot = 0; slot < completedBuildings; slot++) if (buildingTypeFor(seed, slot) === "cottage") homes++;
  return { homes, places: completedBuildings - homes };
}
