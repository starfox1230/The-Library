// Small original vector illustrations, all anchored at the same ground point.
// Keep each silhouette within its lot so neighboring buildings remain legible.
export function drawLandmark(type, variant = 0) {
  const g = new PIXI.Graphics();
  g.ellipse(3, 7, 39, 13).fill({ color: 0x355b42, alpha: .14 });
  diamond(g, 0, 2, 74, 38, 0xd8cdae);
  switch (type) {
    case "school": school(g); break;
    case "fire-station": fireStation(g); break;
    case "church": church(g); break;
    case "temple": temple(g); break;
    case "museum": museum(g); break;
    case "library": library(g); break;
    case "clinic": clinic(g); break;
    case "town-hall": townHall(g); break;
    case "greenhouse": greenhouse(g); break;
    case "observatory": observatory(g); break;
    case "theater": theater(g); break;
    case "market": market(g, variant); break;
    case "bakery": shop(g, false); break;
    case "cafe": shop(g, true); break;
    case "park": park(g); break;
    default: throw new Error(`Unknown landmark: ${type}`);
  }
  return g;
}

function diamond(g, x, y, width, height, color) {
  g.poly([x, y - height / 2, x + width / 2, y, x, y + height / 2, x - width / 2, y]).fill(color);
}

function block(g, width, height, left, right, roof) {
  g.poly([-width, -height, 0, width / 2 - height, 0, width / 2, -width, 0]).fill(left);
  g.poly([0, width / 2 - height, width, -height, width, 0, 0, width / 2]).fill(right);
  diamond(g, 0, -height, width * 2, width, roof);
}

function pane(g, x, y, width = 6, height = 9, slope = .5, color = 0xa9cbd0) {
  g.poly([x, y, x + width, y + width * slope, x + width, y + height + width * slope, x, y + height]).fill(color);
}

function pitchedRoof(g, width, height, light, dark) {
  const back = [-width / 2, -width / 4 - height - 15], front = [width / 2, width / 4 - height - 15];
  g.poly([width, -height, 0, width / 2 - height, ...front]).fill(0xe9d8b8);
  g.poly([0, -width / 2 - height, width + 2, -height, ...front, ...back]).fill(light);
  g.poly([...back, ...front, 0, width / 2 - height + 2, -width - 2, -height]).fill(dark);
  g.moveTo(...back).lineTo(...front).stroke({ color: light, width: 2, cap: "round" });
}

function windows(g, width, height, rows = 1) {
  for (let row = 0; row < rows; row++) for (let i = 0; i < 3; i++) {
    const x = -width + 5 + i * 8;
    pane(g, x, -height + 7 + (x + width) * .5 + row * 12, 5, 7);
    pane(g, 4 + i * 8, width / 2 - height + 5 - i * 4 + row * 12, 5, 7, -.5);
  }
}

function school(g) {
  block(g, 30, 25, 0xecc991, 0xcaa777, 0x5a7f8b);
  windows(g, 30, 25);
  pitchedRoof(g, 31, 25, 0x7197a0, 0x4c7482);
  // Bell tower, brass bell, and a flying school flag.
  g.roundRect(-8, -62, 15, 30, 1).fill(0xf7dfae);
  g.roundRect(-4, -56, 7, 10, 3).fill(0x7a7a65);
  g.poly([-3, -50, 2, -50, 4, -46, -5, -46]).fill(0xe1b25f);
  g.poly([-12, -62, 0, -73, 11, -62]).fill(0x4c7482);
  g.moveTo(0, -73).lineTo(0, -88).stroke({ color: 0x7f8572, width: 1.5 });
  g.poly([1, -88, 13, -85, 1, -81]).fill(0xdd8d71);
  pane(g, 5, -5, 8, 14, -.5, 0x657c7a);
}

function fireStation(g) {
  block(g, 32, 27, 0xd99a7a, 0xb76453, 0xe5c69d);
  for (let i = 0; i < 2; i++) {
    const x = 3 + i * 14, y = -8 - i * 7;
    pane(g, x, y, 12, 19, -.5, 0x933f39);
    for (let row = 0; row < 4; row++) g.moveTo(x + 1, y + 3 + row * 4).lineTo(x + 11, y - 2 + row * 4).stroke({ color: 0xc97f63, width: .9 });
  }
  g.roundRect(-24, -60, 15, 34, 1).fill(0xd5ab80);
  g.poly([-27, -60, -17, -66, -6, -60, -17, -54]).fill(0xb9634c);
  g.roundRect(-21, -53, 9, 11, 2).fill(0x6b8e91);
  for (let i = 0; i < 3; i++) g.moveTo(-24, -37 - i * 5).lineTo(-9, -37 - i * 5).stroke({ color: 0xe8cda4, width: 1.2 });
  // A parked fire engine: glazed cab, hose stripe, ladder, and dark wheels.
  g.roundRect(-15, 10, 25, 11, 2).fill(0xc95145);
  g.roundRect(-12, 7, 11, 9, 2).fill(0xe17558);
  g.roundRect(-11, 8, 8, 5, 1).fill(0xc4e0d8);
  g.moveTo(-13, 17).lineTo(8, 17).stroke({ color: 0xffe4a1, width: 1.6 });
  g.moveTo(0, 9).lineTo(10, 9).stroke({ color: 0xd5d4bc, width: 2 });
  g.circle(-8, 21, 3).circle(5, 21, 3).fill(0x505d56);
  g.circle(-7, 6, 1.8).fill(0xe7b76c);
}

function church(g) {
  block(g, 32, 22, 0xf1e9d8, 0xd8d5c9, 0x708c91);
  pitchedRoof(g, 33, 22, 0x879da0, 0x607b81);
  for (let i = 0; i < 3; i++) {
    pane(g, -27 + i * 8, -18 + i * 4, 5, 9, .5, 0x94b7bb);
    pane(g, 5 + i * 8, -8 - i * 4, 5, 9, -.5, 0x94b7bb);
  }
  pane(g, 8, -7, 9, 15, -.5, 0x6d8584);
  // A modest ward chapel with a tall steeple and simple gold finial.
  g.roundRect(-8, -55, 16, 29, 1).fill(0xf7f0df);
  g.poly([-12, -55, 0, -69, 12, -55]).fill(0x708c91);
  g.roundRect(-2, -50, 5, 8, 2).fill(0xa9c7c7);
  g.circle(0, -72, 2.2).fill(0xd9b467);
  g.moveTo(0, -70).lineTo(0, -68).stroke({ color: 0xd9b467, width: 1.4 });
}

function temple(g) {
  block(g, 32, 27, 0xf7f0df, 0xe2ddcf, 0xb8b49f);
  // A distant, carefully symmetrical temple with a taller central tower.
  for (const x of [-22, -11, 11, 22]) {
    g.roundRect(x - 2, -42, 4, 24, 1).fill(0xfaf5e8);
    g.circle(x, -45, 3).fill(0xe4d7b5);
    g.poly([x - 4, -47, x, -55, x + 4, -47]).fill(0xc5bea8);
  }
  g.roundRect(-6, -66, 12, 43, 1).fill(0xf8f2e4);
  g.poly([-9, -66, 0, -80, 9, -66]).fill(0xb8b49f);
  g.poly([-31, -44, 0, -58, 31, -44, 0, -32]).fill(0xf2ead6);
  g.moveTo(-25, -39).lineTo(25, -39).stroke({ color: 0xd5c394, width: 1.5 });
  g.circle(0, -83, 2.5).fill(0xd9b467);
  pane(g, -3, -32, 6, 11, .5, 0x91aeb2);
}

function museum(g) {
  block(g, 32, 29, 0xede4ce, 0xd5cbb3, 0xc0b49a);
  // Classical pediment and four columns, with an inset doorway behind them.
  pane(g, 10, -9, 11, 16, -.5, 0x688c8b);
  for (let i = 0; i < 4; i++) {
    const x = 3 + i * 8, y = -17 - i * 4;
    g.roundRect(x, y, 3.5, 23, 1).fill(0xfff2d4);
    pane(g, x - 1, y - 2, 6, 3, -.5, 0xe9d5af);
    pane(g, x - 1, y + 21, 6, 3, -.5, 0xf9e7c5);
  }
  g.poly([-2, -19, 35, -37.5, 16, -50]).fill(0xf0dec0);
  g.poly([5, -24, 28, -35.5, 16, -43]).fill(0xc9b89a);
  g.circle(16, -36, 2.6).fill(0xe5cb91);
  pane(g, -26, -25, 10, 13, .5, 0xc1d0c7);
  pane(g, -13, -18.5, 8, 13, .5, 0xc1d0c7);
}

function library(g) {
  block(g, 30, 35, 0xd4a681, 0xac7d65, 0x71908a);
  // Tall glazed reading-room windows and rows of books visible through them.
  for (let i = 0; i < 3; i++) {
    const x = -25 + i * 8, y = -29 + i * 4;
    pane(g, x, y, 6, 18, .5, 0xd0e0cf);
    for (let book = 0; book < 3; book++) pane(g, x + 1 + book * 1.6, y + 8 + book * .8, 1.2, 6, .5, [0xb7725e, 0x658d90, 0xcca863][book]);
  }
  pane(g, 4, -9, 9, 18, -.5, 0x6a8884);
  pane(g, 17, -28, 10, 12, -.5, 0xcee1d6);
  // Open-book plaque above the entrance.
  g.poly([4, -24, 12, -22, 12, -13, 4, -16]).fill(0xffecc5);
  g.poly([12, -22, 20, -28, 20, -19, 12, -13]).fill(0xe6cda1);
  g.moveTo(12, -21).lineTo(12, -14).stroke({ color: 0xaa986f, width: 1 });
}

function clinic(g) {
  block(g, 29, 28, 0xf6ecd7, 0xdcdcc9, 0x94b7a1);
  windows(g, 29, 28);
  pane(g, 11, -6, 9, 15, -.5, 0x83a7a0);
  g.roundRect(-9, -43, 20, 18, 2).fill(0xfff4df);
  g.roundRect(-2, -40, 6, 13, 1).roundRect(-6, -36, 14, 5, 1).fill(0x689c80);
  pane(g, -29, -5, 30, 4, .5, 0x7fa68e);
}

function townHall(g) {
  block(g, 32, 32, 0xeee0bf, 0xd5c4a1, 0x6e9390);
  windows(g, 32, 32, 2);
  pitchedRoof(g, 33, 32, 0x7c9d99, 0x527e7e);
  g.roundRect(-7, -77, 17, 39, 1).fill(0xf7e5bc);
  g.poly([-11, -77, 1, -92, 14, -77]).fill(0x527e7e);
  g.circle(1, -65, 6).fill(0xfff8df);
  g.moveTo(1, -69).lineTo(1, -65).lineTo(4, -63).stroke({ color: 0x68776a, width: 1.3 });
  pane(g, 5, -3, 10, 15, -.5, 0x738f82);
}

function greenhouse(g) {
  block(g, 30, 23, 0xb4d3b2, 0x97bdb3, 0xd4e7cf);
  pitchedRoof(g, 31, 23, 0xc2dcd2, 0x9cc6bb);
  for (let i = 0; i < 4; i++) {
    const x = -28 + i * 7;
    pane(g, x, -19 + i * 3.5, 5, 16, .5, 0xc7e2c4);
    g.moveTo(x - 1, -23 + i * 3.5).lineTo(x - 1, i * 3.5).stroke({ color: 0xf5ecd4, width: 1.5 });
    g.ellipse(x + 2, -8 + i * 3.5, 2, 4).fill(0x76a76d);
    pane(g, 2 + i * 7, -9 - i * 3.5, 5, 16, -.5, 0xaed8c5);
  }
  g.moveTo(-16, -46).lineTo(16, -30).moveTo(-29, -23).lineTo(1, -8).stroke({ color: 0xf5ecd4, width: 1.7 });
}

function observatory(g) {
  block(g, 28, 20, 0xe4e0c7, 0xc0c7ba, 0x8aabae);
  g.moveTo(-26, -23).quadraticCurveTo(-25, -62, 0, -65).quadraticCurveTo(25, -61, 27, -24).closePath().fill(0x7f9eb4);
  g.ellipse(0, -24, 27, 8).fill(0x587e98);
  g.moveTo(-1, -64).quadraticCurveTo(9, -44, 7, -28).stroke({ color: 0xc2d5dd, width: 2 });
  g.moveTo(8, -48).lineTo(31, -62).stroke({ color: 0xf2e4c8, width: 6, cap: "round" });
  g.circle(31, -62, 3.6).fill(0x416978);
  pane(g, 9, -3, 8, 13, -.5, 0x71919c);
}

function theater(g) {
  block(g, 31, 33, 0xb28d91, 0x8c6e82, 0x5c667c);
  pane(g, 4, -6, 21, 18, -.5, 0x6c4b59);
  pane(g, 5, -5, 8, 17, -.5, 0xb76567);
  pane(g, 16, -10.5, 8, 17, -.5, 0xb76567);
  pane(g, 0, -21, 33, 9, -.5, 0xf0d69b);
  for (let i = 0; i < 7; i++) g.circle(2 + i * 4.8, -19 - i * 2.4, 1.1).fill(0xfff5cb);
  g.moveTo(-23, -33).lineTo(-23, -47).stroke({ color: 0xd9bc8a, width: 2 });
  g.poly([-22, -47, -11, -44, -22, -39]).fill(0xdf9a83);
  pane(g, -25, -28, 16, 15, .5, 0xebc7a1);
}

function market(g, variant) {
  for (const [x, y] of [[-29, 0], [0, 15], [29, 0], [0, -15]]) g.moveTo(x, y).lineTo(x, y - 26).stroke({ color: 0x967b58, width: 2 });
  for (let i = 0; i < 6; i++) {
    const x = -32 + i * 32 / 6, y = -28 + i * 16 / 6;
    g.poly([x, y, x + 32 / 6, y + 16 / 6, x + 32 / 6 + 32, y + 16 / 6 - 16, x + 32, y - 16]).fill(i % 2 ? 0xf6e8c4 : [0xc98166, 0x759889][variant % 2]);
  }
  for (let i = 0; i < 3; i++) {
    diamond(g, -17 + i * 13, 5 + i * 2, 19, 10, 0xa58459);
    for (let j = 0; j < 3; j++) g.circle(-22 + i * 13 + j * 4, 2 + i * 2, 2.2).fill([0xda9b61, 0x90ae65, 0xc87d68][i]);
  }
}

function shop(g, coffee) {
  block(g, 27, 25, 0xf0d6ab, 0xd5b88e, coffee ? 0x6c938b : 0xc98765);
  pitchedRoof(g, 28, 25, coffee ? 0x82a89c : 0xe0a17a, coffee ? 0x527e78 : 0xb66e53);
  pane(g, 3, -3, 8, 14, -.5, 0x6c857b);
  pane(g, 14, -13, 10, 11, -.5, 0xb7d2bf);
  for (let i = 0; i < 5; i++) {
    const x = -28 + i * 5.6;
    g.poly([x, -17 + i * 2.8, x + 5.6, -14.2 + i * 2.8, x + 1.6, -7.2 + i * 2.8, x - 4, -10 + i * 2.8]).fill(i % 2 ? 0xffecc9 : coffee ? 0x69948b : 0xd99578);
  }
  if (coffee) {
    g.roundRect(-15, -34, 11, 8, 2).fill(0xfff0cf);
    g.ellipse(-3, -30, 3, 2.5).stroke({ color: 0xfff0cf, width: 1.4 });
    g.moveTo(29, 8).lineTo(29, -7).stroke({ color: 0xa88b62, width: 1.3 });
    g.poly([17, -7, 29, -16, 41, -7, 29, -3]).fill(0xe6c48b);
    g.ellipse(29, 8, 7, 3).fill(0xd2b88b);
  } else {
    g.ellipse(-11, -29, 10, 5).fill(0xf1cb82);
    for (let i = 0; i < 3; i++) g.moveTo(-16 + i * 4, -31).lineTo(-14 + i * 4, -27).stroke({ color: 0xb88a50, width: 1 });
  }
}

function park(g) {
  diamond(g, 0, 1, 69, 35, 0xa4bd86);
  g.ellipse(0, 3, 17, 9).fill(0xd3d6bf);
  g.ellipse(0, 1, 14, 6.5).fill(0x7fb9bc);
  g.ellipse(0, -3, 7, 3.5).fill(0xdde0c8);
  g.moveTo(0, -4).lineTo(0, -20).stroke({ color: 0xd8eddd, width: 2.6 });
  g.moveTo(0, -17).quadraticCurveTo(-8, -22, -9, -5).moveTo(0, -17).quadraticCurveTo(8, -22, 9, -5).stroke({ color: 0xc6e3d6, width: 1.3 });
  for (const side of [-1, 1]) {
    const x = side * 25;
    g.moveTo(x - 5, 9).lineTo(x - 5, 3).moveTo(x + 5, 9).lineTo(x + 5, 3).stroke({ color: 0x7d8066, width: 1.5 });
    g.roundRect(x - 7, 0, 14, 4, 1).roundRect(x - 7, -5, 14, 3, 1).fill(0xb49767);
    g.moveTo(x, -3).lineTo(x, -19).stroke({ color: 0x977d57, width: 2 });
    g.circle(x, -17, 6).circle(x - 2, -23, 5).fill(side < 0 ? 0x759d6b : 0x8fb476);
  }
}
