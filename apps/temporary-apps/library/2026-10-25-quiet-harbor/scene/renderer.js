const TILE_X = 58;
const TILE_Y = 31;

const GROUND = ["landscapeTiles_010", "landscapeTiles_015", "landscapeTiles_016", "landscapeTiles_022", "landscapeTiles_067", "landscapeTiles_075"];
const HOUSES = ["buildingTiles_001", "buildingTiles_002", "buildingTiles_009", "buildingTiles_010", "buildingTiles_012", "buildingTiles_014", "buildingTiles_016", "buildingTiles_017", "buildingTiles_018", "buildingTiles_020", "buildingTiles_021", "buildingTiles_025", "buildingTiles_026", "buildingTiles_027", "buildingTiles_030", "buildingTiles_033", "buildingTiles_034", "buildingTiles_040", "buildingTiles_041", "buildingTiles_046", "buildingTiles_092", "buildingTiles_093"];
const CIVIC = ["cityTiles_036", "cityTiles_044", "cityTiles_043"];

export class IslandRenderer {
  constructor(host) {
    this.host = host;
    this.app = null;
    this.catalog = null;
    this.textures = new Map();
    this.worldRoot = null;
    this.water = null;
    this.residentLayer = null;
    this.residents = [];
    this.effectLayer = null;
    this.seedPlant = null;
    this.visualKey = "";
    this.camera = { x: 0, y: 0, zoom: 0.77 };
    this.pointer = new Map();
    this.drag = null;
    this.onCameraChange = null;
    this.onSelectBuilding = null;
    this.lastWorld = null;
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(host);
  }

  async init(savedCamera) {
    this.catalog = await (await fetch("./assets/catalog.json")).json();
    for (const [pack, value] of Object.entries(this.catalog.packs)) {
      const frames = new Map();
      await Promise.all(Object.entries(value.frames).map(async ([name, image]) => frames.set(name, await PIXI.Assets.load(image.src))));
      this.textures.set(pack, frames);
    }
    this.app = new PIXI.Application();
    await this.app.init({ backgroundAlpha: 0, antialias: true, autoDensity: true, resolution: Math.min(globalThis.devicePixelRatio || 1, 2), preference: "webgl", powerPreference: "low-power" });
    this.app.canvas.setAttribute("aria-hidden", "true");
    this.host.append(this.app.canvas);
    this.worldRoot = new PIXI.Container({ sortableChildren: true });
    this.residentLayer = new PIXI.Container();
    this.effectLayer = new PIXI.Container();
    this.water = this.buildWater();
    this.app.stage.addChild(this.water, this.worldRoot, this.effectLayer, this.residentLayer);
    const savedX = savedCamera?.centerX ?? savedCamera?.x, savedY = savedCamera?.centerY ?? savedCamera?.y;
    this.camera = savedCamera && Number.isFinite(savedX) && Number.isFinite(savedY) && Number.isFinite(savedCamera.zoom)
      ? { x: savedX, y: savedY, zoom: Math.max(.5, Math.min(1.65, savedCamera.zoom)) }
      : this.camera;
    this.bindGestures();
    this.app.ticker.maxFPS = 30;
    this.app.ticker.add((ticker) => this.animate(ticker.deltaMS));
    this.resize();
    return this;
  }

  buildWater() {
    const group = new PIXI.Container();
    for (let i = 0; i < 18; i++) {
      const point = new PIXI.Graphics().ellipse(0, 0, 2.6 + (i % 3), .85).fill({ color: 0xd2eee0, alpha: .27 });
      point.__nx = ((i * 79 + 31) % 401) / 401;
      point.__ny = ((i * 137 + 21) % 307) / 307;
      point.alpha = .2 + (i % 4) * .08;
      point.__phase = i * .7;
      group.addChild(point);
    }
    return group;
  }

  bindGestures() {
    const surface = this.host;
    surface.addEventListener("pointerdown", (event) => {
      if (event.target.closest("button")) return;
      if (this.pointer.size > 1) this.pointer.clear();
      this.pointer.set(event.pointerId, { x: event.clientX, y: event.clientY });
      try { surface.setPointerCapture(event.pointerId); } catch { /* native scroll or a second finger can take capture */ }
      if (this.pointer.size === 1) this.drag = { id: event.pointerId, x: event.clientX, y: event.clientY, startX: event.clientX, startY: event.clientY, moved: false };
      if (this.pointer.size === 2) {
        const pts = [...this.pointer.values()];
        this.drag = { pinch: true, distance: Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y), zoom: this.camera.zoom };
      }
    });
    surface.addEventListener("pointermove", (event) => {
      if (!this.pointer.has(event.pointerId)) return;
      this.pointer.set(event.pointerId, { x: event.clientX, y: event.clientY });
      if (this.pointer.size === 2 && this.drag?.pinch) {
        const pts = [...this.pointer.values()];
        const dist = Math.max(1, Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y));
        this.camera.zoom = clamp(this.drag.zoom * dist / this.drag.distance, .5, 1.65);
        this.placeWorld(); this.notifyCamera(); return;
      }
      if (!this.drag || this.drag.id !== event.pointerId) return;
      const dx = event.clientX - this.drag.x, dy = event.clientY - this.drag.y;
      if (Math.hypot(event.clientX - this.drag.startX, event.clientY - this.drag.startY) > 5) this.drag.moved = true;
      if (this.drag.moved) {
        const rect = this.host.getBoundingClientRect(), scale = Math.max(.4, this.camera.zoom);
        const worldDx = dx * rect.width / this.app.screen.width / scale;
        const worldDy = dy * rect.height / this.app.screen.height / scale;
        this.camera.x -= worldDx / TILE_X + worldDy / TILE_Y;
        this.camera.y += worldDx / TILE_X - worldDy / TILE_Y;
        this.drag.x = event.clientX; this.drag.y = event.clientY;
        this.placeWorld(); this.notifyCamera();
      }
    });
    const finish = (event) => {
      if (!this.pointer.has(event.pointerId)) return;
      const prior = this.drag;
      this.pointer.delete(event.pointerId);
      if (this.pointer.size < 2 && prior?.pinch) this.drag = null;
      else if (prior && !prior.pinch && prior.id === event.pointerId) {
        if (!prior.moved) this.selectAt(event.clientX, event.clientY);
        this.drag = null;
      }
    };
    surface.addEventListener("pointerup", finish);
    surface.addEventListener("pointercancel", (event) => { this.pointer.delete(event.pointerId); this.drag = null; });
    surface.addEventListener("lostpointercapture", (event) => { this.pointer.delete(event.pointerId); if (!this.pointer.size) this.drag = null; });
  }

  selectAt(clientX, clientY) {
    if (!this.lastWorld || !this.onSelectBuilding) return;
    const rect = this.host.getBoundingClientRect();
    const sx = (clientX - rect.left - rect.width / 2) * this.app.screen.width / rect.width;
    const sy = (clientY - rect.top - rect.height / 2) * this.app.screen.height / rect.height;
    const wx = sx / this.camera.zoom, wy = sy / this.camera.zoom;
    const gx = wx / TILE_X + wy / TILE_Y + this.camera.x;
    const gy = -wx / TILE_X + wy / TILE_Y + this.camera.y;
    const nearest = this.lastWorld.buildings.reduce((best, item) => {
      const distance = Math.hypot(item.x - gx, item.y - gy);
      return distance < best.distance ? { item, distance } : best;
    }, { item: null, distance: 1.3 });
    if (nearest.item) this.onSelectBuilding(nearest.item);
  }

  async renderWorld(world) {
    if (!this.app) return;
    this.lastWorld = world;
    const key = `${world.seed}:${world.growth.stageId}:${world.growth.completedBuildings}:${Math.floor(world.growth.elapsedSeconds / 30)}`;
    if (key === this.visualKey) return;
    this.visualKey = key;
    this.worldRoot.removeChildren();
    this.residentLayer.removeChildren();
    this.residents = [];
    this.effectLayer.removeChildren();
    const [land, buildings, city] = [this.textures.get("landscape"), this.textures.get("buildings"), this.textures.get("city")];
    const radius = Math.max(4, world.terrainRadius);
    const extent = Math.ceil(radius + 3);
    const visible = this.visibleGridBounds(extent);
    const objects = [];
    for (let x = visible.minX; x <= visible.maxX; x++) for (let y = visible.minY; y <= visible.maxY; y++) {
      const tile = terrainFrame(world.seed, x, y, land);
      if (!isLand(world.seed, x, y, radius)) continue;
      const sprite = new PIXI.Sprite(tile);
      sprite.anchor.set(.5, .84);
      sprite.x = x * TILE_X / 2 - y * TILE_X / 2;
      sprite.y = x * TILE_Y / 2 + y * TILE_Y / 2;
      sprite.zIndex = Math.round(sprite.y * 100 + x);
      sprite.scale.set(.98);
      objects.push(sprite);
      const growthChance = Math.min(.2, world.growth.elapsedSeconds / 90_000);
      const groveRoll = hash(`${world.seed}:grove:${x}:${y}`) / 0x1_0000_0000;
      if (Math.hypot(x, y) > 2.5 && groveRoll < growthChance && hash(`${world.seed}:tree:${x}:${y}`) % 3 === 0) {
        objects.push(this.makeTree(x, y, hash(`${world.seed}:tree-color:${x}:${y}`)));
      }
    }
    for (const home of world.buildings) {
      if (home.x < visible.minX || home.x > visible.maxX || home.y < visible.minY || home.y > visible.maxY) continue;
      const ageSeconds = world.growth.elapsedSeconds;
      const inProgress = ageSeconds < home.birthAtSeconds;
      if (ageSeconds < home.startsAtSeconds) continue;
      const assetName = home.kind === "civic" ? CIVIC[home.variant % CIVIC.length] : HOUSES[home.variant % HOUSES.length];
      const textures = home.kind === "civic" ? city : buildings;
      const sprite = new PIXI.Sprite(textures.get(assetName) || textures.values().next().value);
      sprite.anchor.set(.5, .84);
      sprite.x = home.x * TILE_X / 2 - home.y * TILE_X / 2;
      sprite.y = home.x * TILE_Y / 2 + home.y * TILE_Y / 2;
      sprite.zIndex = Math.round(sprite.y * 100 + home.x + 1);
      const construction = Math.max(0, Math.min(1, (ageSeconds - home.startsAtSeconds) / home.buildSeconds));
      sprite.alpha = inProgress ? .42 + .38 * construction : 1;
      sprite.scale.set(inProgress ? .82 + .18 * construction : 1);
      objects.push(sprite);
      if (home.kind === "home" && hash(home.id) % 4 === 0 && !inProgress) objects.push(this.makeGarden(home, objects.length));
    }
    for (const item of objects) this.worldRoot.addChild(item);
    this.drawStartingGarden(world, land);
    this.drawResidents(world);
    this.placeWorld();
    this.notifyCamera();
  }

  visibleGridBounds(extent) {
    if (!this.app) return { minX: -extent, maxX: extent, minY: -extent, maxY: extent };
    const diagonal = (this.app.screen.width / (TILE_X * this.camera.zoom) + this.app.screen.height / (TILE_Y * this.camera.zoom)) / 2 + 5;
    const reach = Math.min(Math.max(extent, 8), Math.ceil(diagonal));
    return { minX: Math.max(-extent, Math.floor(this.camera.x - reach)), maxX: Math.min(extent, Math.ceil(this.camera.x + reach)), minY: Math.max(-extent, Math.floor(this.camera.y - reach)), maxY: Math.min(extent, Math.ceil(this.camera.y + reach)) };
  }

  drawStartingGarden(world, land) {
    const layer = new PIXI.Container();
    const elapsed = world.growth.elapsedSeconds;
    const central = new PIXI.Graphics().ellipse(0, 0, 53, 24).fill({ color: 0xd2c893, alpha: .92 });
    central.x = 8; central.y = 12; central.zIndex = 1_000_000;
    layer.addChild(central);
    const plant = new PIXI.Graphics();
    if (elapsed < 10) {
      plant.ellipse(8, 14, 5, 2.7).fill(0x875d3f);
      plant.ellipse(10, 15, 2, 1.1).fill(0xc79762);
    } else {
      const h = elapsed < 30 ? 8 + (elapsed - 10) * .4 : 18 + Math.min(18, Math.log2(elapsed / 30 + 1) * 3);
      plant.moveTo(8, 20).lineTo(9, 20 - h).stroke({ color: 0x557e57, width: 3.4, cap: "round" });
      plant.ellipse(3, 20 - h + 4, Math.min(9, h * .34), Math.min(4, h * .16)).fill(0x91b979);
      if (elapsed >= 30) plant.ellipse(14, 17 - h, 7, 3.4).fill(0xaed08a);
      plant.ellipse(9, 21 - h, 3.8, 3.8).fill(0x69915e);
    }
    plant.x = 9; plant.y = -4; plant.zIndex = 1_000_010;
    layer.sortableChildren = true; layer.addChild(plant); layer.zIndex = 1_000_000; this.worldRoot.addChild(layer);
    if (world.growth.gardenPresent) {
      const garden = new PIXI.Container(); garden.x = -64; garden.y = 35; garden.zIndex = 1_000_020;
      for (let i = 0; i < 5; i++) {
        const flower = new PIXI.Graphics().ellipse(0, 0, 7, 3).fill(i % 2 ? 0xb8c87b : 0xd4a46d);
        flower.x = (i - 2) * 10; flower.y = Math.abs(i - 2) * 3; garden.addChild(flower);
      }
      this.worldRoot.addChild(garden);
    }
    if (elapsed >= 180) {
      const path = new PIXI.Graphics().moveTo(-105, 63).bezierCurveTo(-61, 45, -43, 54, 8, 23).stroke({ color: 0xead9b2, width: 5, alpha: .86 });
      path.zIndex = 800_000; this.worldRoot.addChild(path);
    }
  }

  makeGarden(home, index) {
    const group = new PIXI.Graphics();
    group.ellipse(-11, 6, 12, 4).fill({ color: 0x807b4d, alpha: .76 });
    group.ellipse(-10, 3, 9, 2.4).fill(0x84a466);
    for (let i = 0; i < 3; i++) group.circle(-14 + i * 4, -1 - (i % 2) * 2, 1.4).fill(i % 2 ? 0xd9bd80 : 0xc7d78a);
    group.x = home.x * TILE_X / 2 - home.y * TILE_X / 2; group.y = home.x * TILE_Y / 2 + home.y * TILE_Y / 2; group.zIndex = group.y * 100 + home.x + 2;
    return group;
  }

  makeTree(x, y, variety) {
    const tree = new PIXI.Graphics();
    const shade = [0x7d9d68, 0x91a96c, 0x698c65, 0xa1ae70][variety % 4];
    tree.ellipse(0, 5, 7, 2.3).fill({ color: 0x264e45, alpha: .24 });
    tree.roundRect(-1.1, -1, 2.2, 8, 1).fill(0x957c5d);
    tree.circle(-2, -5, 4.6).fill(shade);
    tree.circle(2.1, -6.2, 4.2).fill(shade);
    tree.circle(.2, -9, 3.8).fill([0x8ea971, 0xa0b878, 0x78976c, 0xb2b77b][variety % 4]);
    tree.x = x * TILE_X / 2 - y * TILE_X / 2;
    tree.y = x * TILE_Y / 2 + y * TILE_Y / 2;
    tree.zIndex = Math.round(tree.y * 100 + x + .5);
    return tree;
  }

  drawResidents(world) {
    for (const resident of world.residents) {
      const group = new PIXI.Container();
      const shadow = new PIXI.Graphics().ellipse(0, 9, 6, 2.7).fill({ color: 0x173b37, alpha: .32 });
      const body = new PIXI.Graphics().roundRect(-4, -1, 8, 10, 3).fill(0xf4dcad);
      const coat = new PIXI.Graphics().roundRect(-4.2, 1, 8.4, 7, 2.7).fill([0x7b9690, 0x947c69, 0x879464, 0x788b9a][resident.id % 4]);
      const head = new PIXI.Graphics().circle(0, -5, 4.1).fill([0xd9a77c, 0xc68d6d, 0xe0b994][resident.id % 3]);
      const hair = new PIXI.Graphics().ellipse(0, -8, 3.8, 1.8).fill(0x533d36);
      group.addChild(shadow, body, coat, head, hair);
      this.residentLayer.addChild(group);
      this.residents.push({ display: group, model: resident });
    }
    this.updateResidents(world.growth.elapsedSeconds);
  }

  updateResidents(seconds) {
    for (const { display, model } of this.residents) {
      const angle = seconds * (.08 + model.id * .004) + model.phase;
      const gx = model.x + Math.cos(angle) * .17;
      const gy = model.y + Math.sin(angle * .7) * .17;
      display.x = gx * TILE_X / 2 - gy * TILE_X / 2;
      display.y = gx * TILE_Y / 2 + gy * TILE_Y / 2;
      display.zIndex = Math.round(display.y * 100 + gx);
    }
  }

  placeWorld() {
    if (!this.app || !this.worldRoot) return;
    const w = this.app.screen.width, h = this.app.screen.height;
    this.worldRoot.scale.set(this.camera.zoom);
    this.worldRoot.position.set(w / 2 - (this.camera.x - this.camera.y) * TILE_X / 2 * this.camera.zoom, h / 2 - (this.camera.x + this.camera.y) * TILE_Y / 2 * this.camera.zoom);
    this.water.children.forEach((p) => { p.x = p.__nx * w; p.y = p.__ny * h; });
    this.water.position.set(0, 0);
  }

  resize() {
    if (!this.app) return;
    const r = this.host.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return;
    this.app.renderer.resize(r.width, r.height);
    this.placeWorld();
  }

  animate(deltaMS) {
    const time = performance.now() / 1000;
    for (const p of this.water.children) {
      p.x = (p.__nx + .008 * Math.sin(time * .33 + p.__phase) + 1) % 1 * this.app.screen.width;
      p.y = (p.__ny + .006 * Math.cos(time * .26 + p.__phase) + 1) % 1 * this.app.screen.height;
      p.alpha = .16 + .13 * (1 + Math.sin(time * .6 + p.__phase)) / 2;
    }
    if (this.lastWorld?.growth.personPresent) this.updateResidents(this.lastWorld.growth.elapsedSeconds + time % 30);
  }

  setZoom(zoom) { this.camera.zoom = clamp(zoom, .5, 1.65); this.placeWorld(); this.notifyCamera(); }
  recenter() {
    const latest = this.lastWorld?.buildings.at(-1);
    this.camera.x = latest?.x ?? 0; this.camera.y = latest?.y ?? 0; this.camera.zoom = this.lastWorld?.growth.completedBuildings > 48 ? .58 : .8;
    this.visualKey = ""; this.renderWorld(this.lastWorld); this.notifyCamera();
  }
  restore(camera) { if (camera) { this.camera = { x: camera.centerX || 0, y: camera.centerY || 0, zoom: camera.zoom || .77 }; this.placeWorld(); } }
  getCameraState() { return { centerX: this.camera.x, centerY: this.camera.y, zoom: this.camera.zoom }; }
  notifyCamera() { this.onCameraChange?.(this.getCameraState()); }
  destroy() { this.resizeObserver.disconnect(); this.app?.destroy(true); this.app = null; }
}

function terrainFrame(seed, x, y, frames) {
  const choices = GROUND;
  const frame = choices[hash(`${seed}:ground:${x}:${y}`) % choices.length];
  return frames.get(frame) || frames.get("landscapeTiles_015") || frames.values().next().value;
}
function isLand(seed, x, y, radius) {
  const r = radius + ((hash(`${seed}:shore:${Math.floor(x / 4)}:${Math.floor(y / 4)}`) % 100) / 100) * 1.3;
  const d = Math.hypot(x / 1.13, y);
  return d <= r && !(d > r - 1 && hash(`${seed}:water:${x}:${y}`) % 5 === 0);
}
function hash(value) { let h=2166136261; for (let i=0;i<value.length;i++){h^=value.charCodeAt(i);h=Math.imul(h,16777619);} return h>>>0; }
function clamp(value, min, max) { return Math.max(min, Math.min(max, value)); }
