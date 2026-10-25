export function hash32(value, seed = 0x9e3779b9) {
  let h = seed >>> 0;
  for (let i = 0; i < String(value).length; i++) {
    h ^= String(value).charCodeAt(i);
    h = Math.imul(h, 0x85ebca6b);
    h ^= h >>> 13;
  }
  h ^= h >>> 16;
  h = Math.imul(h, 0x7feb352d);
  h ^= h >>> 15;
  return (h >>> 0) || 0xa341316c;
}

export function randomFor(seed, key) {
  let state = hash32(`${seed}:${key}`);
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let t = state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4_294_967_296;
  };
}

export function seedHex() {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return [...bytes].map((n) => n.toString(16).padStart(2, "0")).join("");
}
