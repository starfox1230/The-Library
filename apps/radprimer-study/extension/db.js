(function (root) {
  'use strict';
  let opening;
  function open() {
    return opening ||= new Promise((resolve, reject) => {
      const request = indexedDB.open('radprimer-case-library-v1', 1);
      request.onupgradeneeded = () => request.result.createObjectStore('cases', { keyPath: 'id' });
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => { opening = null; reject(request.error); };
    });
  }
  async function transact(mode, fn) {
    const db = await open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction('cases', mode); let result;
      tx.oncomplete = () => resolve(result);
      tx.onerror = () => reject(tx.error || new Error('Could not save the library.'));
      tx.onabort = () => reject(tx.error || new Error('Library transaction cancelled.'));
      fn(tx.objectStore('cases'), value => { result = value; });
    });
  }
  const all = () => transact('readonly', (s, done) => { s.getAll().onsuccess = e => done(e.target.result); });
  const get = id => transact('readonly', (s, done) => { s.get(id).onsuccess = e => done(e.target.result); });
  const saveCapture = (capture, options = {}) => transact('readwrite', (s, done) => {
    s.get(capture.id).onsuccess = e => {
      const c = RadCore.mergeCapture(e.target.result, capture);
      if (options.notes?.trim()) c.notes = c.notes ? c.notes + '\n\n' + options.notes.trim() : options.notes.trim();
      if (options.highlights?.length) c.highlights = [...new Set([...c.highlights, ...options.highlights])];
      if (options.anki) { c.ankiStatus = 'queued'; c.tier = 'essential'; }
      s.put(c); done(c);
    };
  });
  const patch = (id, changes) => transact('readwrite', (s, done) => {
    s.get(id).onsuccess = e => {
      if (!e.target.result) return;
      const allowed = ['notes','highlights','tier','ankiStatus','reviewedAt','dueAt','archived'];
      const c = { ...e.target.result, updatedAt: RadCore.now() };
      for (const k of allowed) if (Object.hasOwn(changes, k)) c[k] = changes[k];
      const valid = RadCore.validateCase(c); s.put(valid); done(valid);
    };
  });
  // Validate every record before starting a single atomic import. Existing personal edits win.
  const importBackup = data => {
    const incoming = RadCore.parseBackup(data);
    return transact('readwrite', (s, done) => {
      for (const c of incoming) s.get(c.id).onsuccess = e => {
        const old = e.target.result;
        if (!old) s.put(c);
        else {
          const merged = RadCore.mergeCapture(old, c);
          merged.notes = old.notes || c.notes;
          merged.highlights = [...new Set([...(old.highlights || []), ...c.highlights])];
          s.put(merged);
        }
      };
      done(incoming.length);
    });
  };
  root.RadDB = { all, get, saveCapture, patch, importBackup };
})(globalThis);
