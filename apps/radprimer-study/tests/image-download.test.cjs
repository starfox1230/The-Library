const test = require('node:test');
const assert = require('node:assert/strict');
const { fixture } = require('./fixtures.cjs');

test('real download function normalizes RadPrimer image/jpg into offline-compatible JPEG data URLs', async () => {
  const { w, dom } = fixture();
  const bytes = new Uint8Array([0xff, 0xd8, 0xff, 0xe0, 0x00, 0x10, 0x4a, 0x46, 0x49, 0x46]);
  let requests = 0;
  try {
    w.fetch = async (url, options) => {
      assert.equal(new URL(url).origin, 'https://app.radprimer.com');
      assert.equal(options.credentials, 'same-origin');
      requests++;
      return { ok: true, blob: async () => new w.Blob([bytes], { type: 'image/jpg' }) };
    };
    // Exercise the production loader, capture, validation and storage together.
    const c = await w.RadCapture.capture(w.document);
    assert.equal(requests, 8);
    for (const image of c.groups.flatMap(g => g.images)) {
      assert.match(image.original, /^data:image\/jpeg;base64,/);
      assert.match(image.annotated, /^data:image\/jpeg;base64,/);
      assert.deepEqual(Buffer.from(image.original.split(',')[1], 'base64'), Buffer.from(bytes));
      assert.equal(image.error, '');
    }
    await w.RadDB.saveCapture(w.RadCore.validateCase(c));
    const saved = await w.RadDB.get(c.id);
    assert.equal(w.RadCore.mediaCount(saved).saved, 4);
    assert.equal(w.RadCore.mediaCount(saved).failed, 0);
    assert.ok(saved.groups.every(g => g.images.every(i => w.RadCore.imageData(i.original) && w.RadCore.imageData(i.annotated))));
  } finally { dom.window.close(); }
});

test('standard JPEG and PNG response types remain unchanged', async () => {
  const { w, dom } = fixture();
  try {
    for (const type of ['image/jpeg', 'image/png', 'image/webp', 'image/gif']) {
      w.fetch = async () => ({ ok: true, blob: async () => new w.Blob(['synthetic raster test bytes'], { type }) });
      const data = await w.RadCapture.fetchImage('/images/synthetic?style=xlarge');
      assert.ok(data.startsWith('data:' + type + ';base64,'));
      assert.equal(w.RadCore.imageData(data), true);
    }
  } finally { dom.window.close(); }
});

test('download failures still reject HTML login responses, SVG, empty images and HTTP errors', async () => {
  const { w, dom } = fixture();
  try {
    for (const type of ['text/html', 'image/svg+xml', 'application/octet-stream']) {
      w.fetch = async () => ({ ok: true, blob: async () => new w.Blob(['not a supported image'], { type }) });
      await assert.rejects(w.RadCapture.fetchImage('/images/synthetic'), /Unsupported image response type/);
    }
    w.fetch = async () => ({ ok: true, blob: async () => new w.Blob([], { type: 'image/jpg' }) });
    await assert.rejects(w.RadCapture.fetchImage('/images/synthetic'), /Empty image/);
    w.fetch = async () => ({ ok: false, status: 401 });
    await assert.rejects(w.RadCapture.fetchImage('/images/synthetic'), /returned 401/);
  } finally { dom.window.close(); }
});
