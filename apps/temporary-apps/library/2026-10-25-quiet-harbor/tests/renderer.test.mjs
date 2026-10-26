import test from "node:test";
import assert from "node:assert/strict";
import { IslandRenderer } from "../scene/renderer.js";
import { worldFor } from "../core/world-v1.js";

// A scene-graph double checks occlusion and camera ownership without a GPU.
// Pixel appearance is reviewed separately in visual-review.html.
class Container {
  constructor(options = {}) {
    Object.assign(this, options);
    this.children = [];
    this.scale = { x: 1, y: 1, set(x, y = x) { this.x = x; this.y = y; } };
    this.position = { set: (x, y) => { this.x = x; this.y = y; } };
  }
  addChild(...children) { for (const child of children) { child.parent = this; this.children.push(child); } }
  removeChildren() { return this.children.splice(0); }
  destroy() { this.destroyed = true; for (const child of this.children) child.destroy(); }
}
class Graphics extends Container {}
for (const method of ["ellipse", "circle", "roundRect", "moveTo", "lineTo", "quadraticCurveTo", "poly", "fill", "stroke"]) Graphics.prototype[method] = function () { return this; };
class Application {
  constructor() {
    this.stage = new Container(); this.screen = { width: 390, height: 300 };
    this.canvas = { setAttribute() {} }; this.ticker = { add() {} };
    this.renderer = { resize: (width, height) => Object.assign(this.screen, { width, height }) };
  }
  async init() {}
}
globalThis.PIXI = { Application, Container, Graphics };
globalThis.ResizeObserver = class { observe() {} disconnect() {} };
const host = { append() {}, addEventListener() {}, getBoundingClientRect: () => ({ width: 390, height: 300 }) };

test("terrain and paths stay below homes, gardens, and residents at every growth stage", async () => {
  const renderer = await new IslandRenderer(host).init();
  for (const age of [0, 600_000, 3_600_000, 172_800_000, 8_640_000_000]) {
    const world = worldFor("renderer-regression", age);
    await renderer.renderWorld(world);
    assert.deepEqual(renderer.worldRoot.children, [renderer.groundLayer, renderer.pathLayer, renderer.propLayer]);
    assert.ok(renderer.groundLayer.children.length > 0);
    for (const home of renderer.propLayer.children.filter((item) => item.label)) {
      assert.equal(home.parent, renderer.propLayer);
      assert.ok(world.buildings.some((item) => item.id === home.label));
    }
    for (const resident of renderer.residents) assert.equal(resident.display.parent.parent, renderer.worldRoot);
    if (world.buildings.length) assert.ok(renderer.propLayer.children.some((item) => item.label === "home-0"));
  }
});

test("panning to a distant district renders its buildings and releases the previous scene objects", async () => {
  const renderer = await new IslandRenderer(host).init();
  const world = worldFor("renderer-regression", 8_640_000_000);
  await renderer.renderWorld(world);
  const oldGround = renderer.groundLayer.children[0];
  const destination = world.buildings.at(-1);
  assert.ok(!renderer.propLayer.children.some((item) => item.label === destination.id));
  renderer.camera.x = destination.x; renderer.camera.y = destination.y;
  renderer.placeWorld();
  assert.ok(renderer.propLayer.children.some((item) => item.label === destination.id));
  assert.equal(oldGround.destroyed, true);
  const ground = renderer.groundLayer.children[0];
  renderer.placeWorld();
  assert.equal(renderer.groundLayer.children[0], ground, "a transform with unchanged bounds must not rebuild the scene");
});

test("reduced motion holds the illustrated scene while elapsed-time rendering continues", async () => {
  const renderer = await new IslandRenderer(host).init();
  await renderer.renderWorld(worldFor("renderer-regression", 600_000));
  renderer.setReducedMotion(true);
  const positions = renderer.residents.map(({ display }) => [display.x, display.y]);
  renderer.animate(1000);
  assert.deepEqual(renderer.residents.map(({ display }) => [display.x, display.y]), positions);
  await renderer.renderWorld(worldFor("renderer-regression", 3_600_000));
  assert.ok(renderer.propLayer.children.some((item) => item.label === "home-0"));
});

test("starting a new island after exploring a distant district brings the seed back into view", async () => {
  const renderer = await new IslandRenderer(host).init();
  const grown = worldFor("old-island", 8_640_000_000);
  await renderer.renderWorld(grown);
  renderer.camera.x = grown.buildings.at(-1).x;
  renderer.camera.y = grown.buildings.at(-1).y;
  renderer.placeWorld();
  await renderer.renderWorld(worldFor("new-island", 0));
  assert.equal(renderer.camera.x, 0);
  assert.equal(renderer.camera.y, 0);
  assert.ok(renderer.groundLayer.children.length > 0);
  assert.equal(renderer.selectableHomes.length, 0);
});
