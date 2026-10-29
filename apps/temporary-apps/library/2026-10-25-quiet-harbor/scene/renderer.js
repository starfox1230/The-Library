import { drawLandmark } from "./landmarks.js";

const TILE_X = 58;
const TILE_Y = 31;

const GARDEN = { x: -1.3, y: 1.3 };
const PALETTES = [
  [0xd98c68, 0xb96951, 0xfff0cf, 0xe7cba9],
  [0x6e9690, 0x4b7572, 0xfff2d7, 0xe5cdb1],
  [0xd0aa70, 0xa87b4e, 0xf9ead4, 0xdcc6af],
  [0x859aab, 0x5d778e, 0xf3ecd9, 0xd5d0be],
];

export class IslandRenderer {
  constructor(host) {
    this.host = host;
    this.app = null;
    this.worldRoot = null;
    this.groundLayer = null;
    this.pathLayer = null;
    this.propLayer = null;
    this.water = null;
    this.residentLayer = null;
    this.residents = [];
    this.construction = [];
    this.selectableHomes = [];
    this.reducedMotion = false;
    this.worldRenderedAt = 0;
    this.effectLayer = null;
    this.seedPlant = null;
    this.visualKey = "";
    this.camera = { x: 0, y: 0, zoom: 0.7 };
    this.pointer = new Map();
    this.drag = null;
    this.onCameraChange = null;
    this.onSelectBuilding = null;
    this.lastWorld = null;
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(host);
  }

  async init(savedCamera) {
    this.app = new PIXI.Application();
    await this.app.init({ backgroundAlpha: 0, antialias: true, autoDensity: true, resolution: Math.min(globalThis.devicePixelRatio || 1, 2), preference: "webgl", powerPreference: "low-power" });
    this.app.canvas.setAttribute("aria-hidden", "true");
    this.host.append(this.app.canvas);
    // Terrain never participates in object depth sorting: grass cannot cover a house.
    this.worldRoot = new PIXI.Container();
    this.groundLayer = new PIXI.Container();
    this.pathLayer = new PIXI.Container();
    this.propLayer = new PIXI.Container({ sortableChildren: true });
    this.residentLayer = this.propLayer;
    this.worldRoot.addChild(this.groundLayer, this.pathLayer, this.propLayer);
    this.effectLayer = new PIXI.Container();
    this.water = this.buildWater();
    this.app.stage.addChild(this.water, this.worldRoot, this.effectLayer);
    const savedX = savedCamera?.centerX ?? savedCamera?.x, savedY = savedCamera?.centerY ?? savedCamera?.y;
    this.camera = savedCamera && Number.isFinite(savedX) && Number.isFinite(savedY) && Number.isFinite(savedCamera.zoom)
      ? { x: savedX, y: savedY, zoom: Math.max(.35, Math.min(1.65, savedCamera.zoom)) }
      : this.camera;
    if (!savedCamera || (savedX === 0 && savedY === 0 && savedCamera.zoom === .77)) {
      this.camera.zoom = clamp((this.host.getBoundingClientRect().width - 32) / 500, .35, .95);
    }
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
        this.camera.zoom = clamp(this.drag.zoom * dist / this.drag.distance, .35, 1.65);
        this.placeWorld(); this.notifyCamera(); return;
      }
      if (!this.drag || this.drag.id !== event.pointerId) return;
      const dx = event.clientX - this.drag.x, dy = event.clientY - this.drag.y;
      if (Math.hypot(event.clientX - this.drag.startX, event.clientY - this.drag.startY) > 5) this.drag.moved = true;
      if (this.drag.moved) {
        const rect = this.host.getBoundingClientRect(), scale = Math.max(.25, this.camera.zoom);
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
    const screenX = (clientX - rect.left) * this.app.screen.width / rect.width;
    const screenY = (clientY - rect.top) * this.app.screen.height / rect.height;
    const hit = [...this.selectableHomes].sort((a, b) => b.display.zIndex - a.display.zIndex).find(({ display }) => {
      const bounds = display.getBounds();
      return screenX >= bounds.x && screenX <= bounds.x + bounds.width && screenY >= bounds.y && screenY <= bounds.y + bounds.height;
    });
    if (hit) { this.onSelectBuilding(hit.home); return; }
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
    if (this.lastWorld && this.lastWorld.seed !== world.seed) {
      this.camera = { x: 0, y: 0, zoom: clamp((this.host.getBoundingClientRect().width - 32) / 500, .35, .95) };
    }
    const sameTime = this.lastWorld?.seed === world.seed && this.lastWorld?.growth.elapsedSeconds === world.growth.elapsedSeconds;
    this.lastWorld = world;
    const radius = Math.max(4, world.terrainRadius);
    const visible = this.visibleGridBounds(Math.ceil(radius + 3));
    const key = `${world.seed}:${world.growth.stageId}:${world.growth.completedBuildings}:${Math.floor(world.growth.elapsedSeconds / 30)}:${Object.values(visible).join(",")}`;
    if (key === this.visualKey) return;
    this.visualKey = key;
    for (const layer of [this.groundLayer, this.pathLayer, this.propLayer, this.effectLayer]) {
      for (const child of layer.removeChildren()) child.destroy({ children: true });
    }
    this.residents = [];
    this.construction = [];
    this.selectableHomes = [];
    if (!sameTime) this.worldRenderedAt = performance.now();
    const waterline = new PIXI.Graphics();
    const shore = new PIXI.Graphics();
    const ground = new PIXI.Graphics();
    this.groundLayer.addChild(waterline, shore, ground);
    const objects = [];
    for (let x = visible.minX; x <= visible.maxX; x++) for (let y = visible.minY; y <= visible.maxY; y++) {
      if (!isLand(world.seed, x, y, radius)) continue;
      const [px, py] = project(x, y);
      const edge = [[1, 0], [0, 1], [-1, 0], [0, -1]].some(([dx, dy]) => !isLand(world.seed, x + dx, y + dy, radius));
      if (edge) {
        diamond(waterline, px, py + 5, TILE_X + 14, TILE_Y + 10, 0xa2d6c5, .15);
        diamond(shore, px, py + 5, TILE_X + 1, TILE_Y + 1, 0x9b9f76);
      }
      const tint = hash(`${world.seed}:ground:${Math.floor(x / 2)}:${Math.floor(y / 2)}`) % 3;
      diamond(ground, px, py, TILE_X + .6, TILE_Y + .6, edge ? [0xe5d4aa, 0xdfcda3, 0xe8d8b2][tint] : [0x92b77b, 0x96ba7e, 0x8eb277][tint]);
      const occupied = world.buildings.some((home) => Math.abs(home.x - x) < 1.7 && Math.abs(home.y - y) < 1.7);
      const inGarden = Math.hypot(x - GARDEN.x, y - GARDEN.y) < 2.2;
      const groveRoll = hash(`${world.seed}:grove:${x}:${y}`) / 0x1_0000_0000;
      if (!edge && !occupied && !inGarden && groveRoll < Math.min(.045, world.growth.elapsedSeconds / 960_000)) {
        objects.push(this.makeTree(x, y, hash(`${world.seed}:tree-color:${x}:${y}`)));
      } else if (!edge && !occupied && !inGarden && groveRoll < .22) {
        ground.moveTo(px - 2, py + 1).lineTo(px - 3, py - 2).moveTo(px - 1, py + 1).lineTo(px + 1, py - 1).stroke({ color: 0x739a67, width: 1, alpha: .45 });
      }
    }
    this.drawPaths(world);
    for (const home of world.buildings) {
      if (home.x < visible.minX || home.x > visible.maxX || home.y < visible.minY || home.y > visible.maxY) continue;
      const ageSeconds = world.growth.elapsedSeconds;
      const inProgress = ageSeconds < home.birthAtSeconds;
      if (ageSeconds < home.startsAtSeconds) continue;
      const sprite = this.makeHome(home);
      this.selectableHomes.push({ display: sprite, home });
      const construction = Math.max(0, Math.min(1, (ageSeconds - home.startsAtSeconds) / home.buildSeconds));
      sprite.alpha = inProgress ? .4 + .6 * construction : 1;
      sprite.scale.set(1, inProgress ? .72 + .28 * construction : 1);
      if (inProgress) this.construction.push({ display: sprite, home });
      objects.push(sprite);
      if ((home.type === "cottage" || !home.type && home.kind === "home") && hash(home.id) % 3 === 0 && !inProgress) objects.push(this.makeGarden(home));
    }
    for (const item of objects) this.propLayer.addChild(item);
    this.drawStartingGarden(world);
    this.drawResidents(world);
    this.placeWorld();
  }

  visibleGridBounds(extent) {
    if (!this.app) return { minX: -extent, maxX: extent, minY: -extent, maxY: extent };
    const diagonal = (this.app.screen.width / (TILE_X * this.camera.zoom) + this.app.screen.height / (TILE_Y * this.camera.zoom)) / 2 + 5;
    const reach = Math.min(Math.max(extent, 8), Math.ceil(diagonal));
    return { minX: Math.max(-extent, Math.floor(this.camera.x - reach)), maxX: Math.min(extent, Math.ceil(this.camera.x + reach)), minY: Math.max(-extent, Math.floor(this.camera.y - reach)), maxY: Math.min(extent, Math.ceil(this.camera.y + reach)) };
  }

  drawPaths(world) {
    if (!world.growth.pathPresent) return;
    const roads = new PIXI.Graphics();
    const homes = world.buildings.filter((home) => world.growth.elapsedSeconds >= home.startsAtSeconds);
    const links = [];
    if (!homes.length) links.push([[GARDEN.x - 1, GARDEN.y + 1], [GARDEN.x, GARDEN.y]]);
    for (let i = 0; i < homes.length; i++) {
      const home = homes[i];
      const previous = i ? homes.slice(0, i).reduce((best, item) => Math.hypot(item.x - home.x, item.y - home.y) < Math.hypot(best.x - home.x, best.y - home.y) ? item : best, homes[0]) : GARDEN;
      links.push([[home.x + .8, home.y + .8], [previous.x + .8, home.y + .8], [previous.x + .8, previous.y + .8]]);
    }
    for (const points of links) {
      for (const [width, color] of [[8, 0xc2b48d], [5.5, 0xf0dfb5]]) {
        points.forEach(([x, y], index) => {
          const [px, py] = project(x, y);
          if (index) roads.lineTo(px, py); else roads.moveTo(px, py);
        });
        roads.stroke({ color, width, cap: "round", join: "round" });
      }
    }
    this.pathLayer.addChild(roads);
  }

  drawStartingGarden(world) {
    const elapsed = world.growth.elapsedSeconds;
    const [x, y] = project(GARDEN.x, GARDEN.y);
    const plot = new PIXI.Graphics();
    diamond(plot, x, y + 1, 52, 28, 0xd6c297);
    diamond(plot, x, y, 42, 22, 0x8e7051);
    this.pathLayer.addChild(plot);
    const plant = new PIXI.Graphics();
    plant.ellipse(0, 1, 5, 2.5).fill({ color: 0x624e37, alpha: .25 });
    if (elapsed < 10) plant.ellipse(0, -1, 4, 2).fill(0xc79d60);
    else {
      const height = elapsed < 30 ? 9 + (elapsed - 10) * .35 : Math.min(34, 18 + Math.log2(elapsed / 30 + 1) * 2);
      plant.moveTo(0, 0).quadraticCurveTo(-2, -height / 2, 1, -height).stroke({ color: 0x49744d, width: 2.8, cap: "round" });
      plant.ellipse(-6, -height * .65, 7, 3.2).fill(0x5d965d);
      plant.ellipse(6, -height * .84, 7, 3.6).fill(0xb4d184);
      if (elapsed >= 300) {
        for (let i = 0; i < 5; i++) plant.circle(1 + Math.cos(i * Math.PI * 2 / 5) * 4, -height - 2 + Math.sin(i * Math.PI * 2 / 5) * 4, 3).fill(0xffe5ad);
        plant.circle(1, -height - 2, 2.6).fill(0xd9a254);
      }
    }
    plant.x = x; plant.y = y; plant.zIndex = depth(GARDEN.x, GARDEN.y);
    this.seedPlant = plant; this.propLayer.addChild(plant);
    if (world.growth.gardenPresent) {
      for (let i = 0; i < 2; i++) this.propLayer.addChild(this.makeGarden({ x: GARDEN.x - .8 + i * .65, y: GARDEN.y + .8, variant: i }));
    }
    if (world.growth.foundationPresent) {
      const [px, py] = project(0, 0);
      const foundation = new PIXI.Graphics();
      diamond(foundation, px, py, 48, 25, 0xbfb99e);
      diamond(foundation, px, py - 2, 39, 20, 0xe5dfc8);
      this.pathLayer.addChild(foundation);
    }
  }

  makeGarden(home) {
    const group = new PIXI.Graphics();
    // Raised soil beds, little planted rows, and blossoms rather than floating dots.
    diamond(group, 0, 3, 31, 16, 0x9d7c57);
    diamond(group, 0, 0, 31, 16, 0xc6a775);
    diamond(group, 0, -1, 25, 12, 0x806046);
    for (let row = 0; row < 2; row++) for (let col = 0; col < 3; col++) {
      const px = -8 + col * 6 + row * 4, py = -2 + row * 4 - col * 2;
      group.moveTo(px, py).lineTo(px, py - 5).stroke({ color: 0x547f4e, width: 1.5 });
      group.ellipse(px - 2, py - 2.5, 2.7, 1.2).fill(0x90b76a);
      group.ellipse(px + 2, py - 4, 2.5, 1.2).fill(0x749c59);
      group.circle(px, py - 6, 2).fill([0xf4c175, 0xeaaa9e, 0xf7e5ba][(row + col + (home.variant || 0)) % 3]);
    }
    const gx = home.x + .9, gy = home.y + .8;
    [group.x, group.y] = project(gx, gy); group.zIndex = depth(gx, gy);
    return group;
  }

  makeHome(home) {
    if (home.type && home.type !== "cottage") {
      const landmark = drawLandmark(home.type, home.variant);
      [landmark.x, landmark.y] = project(home.x, home.y);
      landmark.zIndex = depth(home.x, home.y); landmark.label = home.id;
      return landmark;
    }
    const house = new PIXI.Graphics();
    const [roof, roofDark, wall, wallDark] = PALETTES[home.variant % PALETTES.length];
    const civic = home.kind === "civic";
    const width = civic ? 31 : 23 + home.variant % 3;
    const floor = civic ? 30 : 23;
    house.ellipse(3, 7, width + 6, 12).fill({ color: 0x355b42, alpha: .14 });
    diamond(house, 0, 2, width * 2 + 9, width + 5, 0xcfc6a5);
    // The base is the ground plane; all depth is above it, never buried in tiles.
    const a = [0, -width / 2 - floor], b = [width, -floor], c = [0, width / 2 - floor], d = [-width, -floor];
    house.poly([...d, ...c, 0, width / 2, -width, 0]).fill(wall);
    house.poly([...c, ...b, width, 0, 0, width / 2]).fill(wallDark);
    const ridgeBack = [-width / 2, -width / 4 - floor - 15], ridgeFront = [width / 2, width / 4 - floor - 15];
    house.poly([...b, ...c, ...ridgeFront]).fill(wall);
    house.poly([...a, ...b, ...ridgeFront, ...ridgeBack]).fill(roof);
    house.poly([...ridgeBack, ...ridgeFront, c[0], c[1] + 2, d[0] - 3, d[1] + 1]).fill(roofDark);
    house.moveTo(...ridgeBack).lineTo(...ridgeFront).stroke({ color: roof, width: 2.5, cap: "round" });
    house.poly([-16, -13, -8, -9, -8, 4, -16, 0]).fill(0x6e7160);
    house.circle(-10, -2, .8).fill(0xf3d48b);
    house.poly([5, -12, 12, -15.5, 12, -8.5, 5, -5]).fill(0xffe6ad);
    house.poly([16, -17.5, 22, -20.5, 22, -13.5, 16, -10.5]).fill(0xffe6ad);
    house.moveTo(8.5, -14).lineTo(8.5, -6.5).moveTo(19, -19).lineTo(19, -11.5).stroke({ color: 0xac986d, width: 1 });
    // Chimney and a small doorstep give each cottage a recognizable silhouette.
    house.poly([-16, -floor - 10, -11, -floor - 7, -11, -floor - 20, -16, -floor - 23]).fill(0xe6cfab);
    house.poly([-11, -floor - 7, -8, -floor - 9, -8, -floor - 22, -11, -floor - 20]).fill(0xb49a78);
    house.poly([-18, -floor - 23, -12, -floor - 26, -6, -floor - 23, -12, -floor - 20]).fill(0xf2ddba);
    house.poly([-18, 1, -8, 6, -13, 9, -23, 4]).fill(0xe4d7b5);
    if (civic) {
      house.roundRect(-5, -62, 12, 29, 1).fill(0xf5e6c5);
      house.poly([-8, -61, 1, -72, 10, -61]).fill(roofDark);
      house.circle(1, -52, 4).fill(0xfff6d9);
      house.moveTo(1, -55).lineTo(1, -52).lineTo(3, -51).stroke({ color: 0x6d7765, width: 1.1 });
    }
    [house.x, house.y] = project(home.x, home.y); house.zIndex = depth(home.x, home.y);
    house.label = home.id;
    return house;
  }

  makeTree(x, y, variety) {
    const tree = new PIXI.Graphics();
    const shade = [0x7d9d68, 0x91a96c, 0x698c65, 0xa1ae70][variety % 4];
    tree.ellipse(0, 5, 7, 2.3).fill({ color: 0x264e45, alpha: .24 });
    tree.roundRect(-1.1, -1, 2.2, 8, 1).fill(0x957c5d);
    tree.circle(-2, -5, 4.6).fill(shade);
    tree.circle(2.1, -6.2, 4.2).fill(shade);
    tree.circle(.2, -9, 3.8).fill([0x8ea971, 0xa0b878, 0x78976c, 0xb2b77b][variety % 4]);
    [tree.x, tree.y] = project(x, y);
    tree.zIndex = depth(x, y);
    tree.scale.set(1.7);
    return tree;
  }

  drawResidents(world) {
    for (const resident of world.residents) {
      const group = new PIXI.Container();
      const shadow = new PIXI.Graphics().ellipse(0, 0, 4, 1.7).fill({ color: 0x173b37, alpha: .2 });
      const body = new PIXI.Graphics().roundRect(-2.5, -7, 5, 7, 2).fill(0x685d50);
      const coat = new PIXI.Graphics().roundRect(-3, -10, 6, 7, 2).fill([0xe3b17c, 0xa7c2b8, 0xedcc8a, 0x8ca9bb][resident.id % 4]);
      const head = new PIXI.Graphics().circle(0, -12, 3).fill([0xd9a77c, 0xc68d6d, 0xe0b994][resident.id % 3]);
      const hair = new PIXI.Graphics().ellipse(0, -14, 3, 1.5).fill(0x635044);
      group.addChild(shadow, body, coat, head, hair);
      this.residentLayer.addChild(group);
      this.residents.push({ display: group, model: resident });
    }
    this.updateResidents(world.growth.elapsedSeconds);
  }

  updateResidents(seconds) {
    for (const { display, model } of this.residents) {
      const destination = this.lastWorld.buildings[(model.id * 7) % this.lastWorld.buildings.length] || { x: .3, y: .3 };
      const travel = (1 + Math.sin(seconds * .065 + model.id * 1.7)) / 2;
      const start = model.id < 2 ? GARDEN : this.lastWorld.buildings[(model.id * 3) % this.lastWorld.buildings.length] || GARDEN;
      const gx = start.x + .8 + (destination.x - start.x) * Math.min(1, travel * 2);
      const gy = start.y + .8 + (destination.y - start.y) * Math.max(0, travel * 2 - 1);
      [display.x, display.y] = project(gx, gy);
      display.zIndex = depth(gx, gy) + 1;
    }
  }

  placeWorld() {
    if (!this.app || !this.worldRoot) return;
    const w = this.app.screen.width, h = this.app.screen.height;
    this.worldRoot.scale.set(this.camera.zoom);
    this.worldRoot.position.set(w / 2 - (this.camera.x - this.camera.y) * TILE_X / 2 * this.camera.zoom, h / 2 - (this.camera.x + this.camera.y) * TILE_Y / 2 * this.camera.zoom);
    this.water.children.forEach((p) => { p.x = p.__nx * w; p.y = p.__ny * h; });
    this.water.position.set(0, 0);
    if (this.lastWorld) void this.renderWorld(this.lastWorld);
  }

  resize() {
    if (!this.app) return;
    const r = this.host.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return;
    this.app.renderer.resize(r.width, r.height);
    this.placeWorld();
  }

  animate(deltaMS) {
    if (this.reducedMotion) return;
    const time = performance.now() / 1000;
    for (const p of this.water.children) {
      p.x = (p.__nx + .008 * Math.sin(time * .33 + p.__phase) + 1) % 1 * this.app.screen.width;
      p.y = (p.__ny + .006 * Math.cos(time * .26 + p.__phase) + 1) % 1 * this.app.screen.height;
      p.alpha = .16 + .13 * (1 + Math.sin(time * .6 + p.__phase)) / 2;
    }
    if (this.lastWorld?.growth.personPresent) this.updateResidents(time);
    if (this.seedPlant) this.seedPlant.rotation = Math.sin(time * 1.1) * .025;
    for (const { display, home } of this.construction) {
      const elapsed = this.lastWorld.growth.elapsedSeconds + (performance.now() - this.worldRenderedAt) / 1000;
      const progress = clamp((elapsed - home.startsAtSeconds) / home.buildSeconds, 0, 1);
      display.alpha = .4 + .6 * progress;
      display.scale.y = .72 + .28 * progress;
    }
  }

  setReducedMotion(value) { this.reducedMotion = Boolean(value); }

  setZoom(zoom) { this.camera.zoom = clamp(zoom, .35, 1.65); this.placeWorld(); this.notifyCamera(); }
  recenter() {
    const latest = this.lastWorld?.buildings.at(-1);
    this.camera.x = latest?.x ?? 0; this.camera.y = latest?.y ?? 0; this.camera.zoom = this.lastWorld?.growth.completedBuildings > 48 ? .58 : .9;
    this.visualKey = ""; this.renderWorld(this.lastWorld); this.notifyCamera();
  }
  restore(camera) { if (camera) { this.camera = { x: camera.centerX || 0, y: camera.centerY || 0, zoom: camera.zoom || .77 }; this.placeWorld(); } }
  getCameraState() { return { centerX: this.camera.x, centerY: this.camera.y, zoom: this.camera.zoom }; }
  notifyCamera() { this.onCameraChange?.(this.getCameraState()); }
  destroy() { this.resizeObserver.disconnect(); this.app?.destroy(true); this.app = null; }
}

function project(x, y) { return [(x - y) * TILE_X / 2, (x + y) * TILE_Y / 2]; }
function depth(x, y) { return Math.round((x + y) * TILE_Y / 2 * 100 + x); }
function diamond(graphics, x, y, width, height, color, alpha = 1) {
  graphics.poly([x, y - height / 2, x + width / 2, y, x, y + height / 2, x - width / 2, y]).fill({ color, alpha });
}
function isLand(seed, x, y, radius) {
  const r = radius + ((hash(`${seed}:shore:${Math.floor(x / 4)}:${Math.floor(y / 4)}`) % 100) / 100) * 1.3;
  const d = Math.hypot(x / 1.13, y);
  return d <= r && !(d > r - 1 && hash(`${seed}:water:${x}:${y}`) % 5 === 0);
}
function hash(value) { let h=2166136261; for (let i=0;i<value.length;i++){h^=value.charCodeAt(i);h=Math.imul(h,16777619);} return h>>>0; }
function clamp(value, min, max) { return Math.max(min, Math.min(max, value)); }
