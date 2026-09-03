const MODALITIES = [
  { key: "xr", label: "Radiograph", query: "radiograph radiology" },
  { key: "ct", label: "CT", query: "CT radiology" },
  { key: "mri", label: "MRI", query: "MRI radiology" }
];
const STATE_KEY = "msk-image-bank-state-v1";
const DB_NAME = "msk-image-bank-v1";
const DB_STORE = "images";
let activeId = PATHOLOGIES[0]?.id;
let activeModality = "xr";
let state = loadState();
let objectUrls = [];
const dbPromise = openImageDb();

function loadState() {
  try { return JSON.parse(localStorage.getItem(STATE_KEY)) || { records: {}, custom: [] }; }
  catch (_) { return { records: {}, custom: [] }; }
}
function persist() { localStorage.setItem(STATE_KEY, JSON.stringify(state)); updateStatus(); }
function allPathologies() { return [...PATHOLOGIES, ...(state.custom || [])]; }
function pathology(id) { return allPathologies().find((item) => item.id === id); }
function recordFor(id) {
  const p = pathology(id);
  if (!state.records[id]) state.records[id] = { favorite:false, notes:"", findings:{...(p?.findings || {})}, images:{xr:[],ct:[],mri:[]} };
  const r = state.records[id]; r.images = r.images || {xr:[],ct:[],mri:[]};
  MODALITIES.forEach((m) => { r.images[m.key] ||= []; r.findings ||= {}; if (r.findings[m.key] === undefined) r.findings[m.key] = p?.findings?.[m.key] || ""; });
  return r;
}
function openImageDb() {
  return new Promise((resolve) => {
    if (!window.indexedDB) return resolve(null);
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(DB_STORE);
    request.onsuccess = () => resolve(request.result); request.onerror = () => resolve(null);
  });
}
function idbPut(id, blob) { return dbPromise.then((db) => new Promise((resolve) => { if (!db) return resolve(); const tx = db.transaction(DB_STORE,"readwrite"); tx.objectStore(DB_STORE).put(blob,id); tx.oncomplete = resolve; tx.onerror = resolve; })); }
function idbGet(id) { return dbPromise.then((db) => new Promise((resolve) => { if (!db) return resolve(null); const tx = db.transaction(DB_STORE,"readonly"); const req = tx.objectStore(DB_STORE).get(id); req.onsuccess = () => resolve(req.result || null); req.onerror = () => resolve(null); })); }
function idbDelete(id) { return dbPromise.then((db) => { if (!db) return; const tx = db.transaction(DB_STORE,"readwrite"); tx.objectStore(DB_STORE).delete(id); }); }
function esc(value) { return String(value ?? "").replace(/[&<>'"]/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;","\"":"&quot;"}[c])); }
function safeUrl(value) { try { const url = new URL(value); return ["http:","https:"].includes(url.protocol) ? url.href : ""; } catch (_) { return ""; } }
function searchUrl(p, modality) { return `https://www.google.com/search?tbm=isch&q=${encodeURIComponent(`${p.q || p.name} ${modality.query}`)}`; }
function isVisible(p) {
  const needle = document.querySelector("#searchInput").value.trim().toLowerCase(), r = recordFor(p.id);
  const favorite = r.favorite || MODALITIES.some((m) => r.images[m.key].some((image) => image.favorite));
  return (!needle || `${p.name} ${p.group} ${p.q}`.toLowerCase().includes(needle)) && (!document.querySelector("#favoritesOnly").checked || favorite);
}
function favoriteCount() { return allPathologies().filter((p) => { const r = recordFor(p.id); return r.favorite || MODALITIES.some((m) => r.images[m.key].some((image) => image.favorite)); }).length; }
function imageCount() { return allPathologies().reduce((total,p) => total + MODALITIES.reduce((n,m) => n + recordFor(p.id).images[m.key].length,0),0); }
function updateStatus() { document.querySelector("#status").textContent = `${allPathologies().length} diagnoses · ${imageCount()} images · ${favoriteCount()} favorites · saved on this device`; }
function showToast(message) { const el = document.querySelector("#toast"); el.textContent = message; el.classList.add("show"); clearTimeout(showToast.timer); showToast.timer = setTimeout(() => el.classList.remove("show"), 1800); }

function renderList() {
  const list = document.querySelector("#pathologyList"), visible = allPathologies().filter(isVisible);
  if (!visible.length) { list.innerHTML = `<div class="empty">No matching diagnoses.</div>`; return; }
  let html = "", group = "";
  visible.forEach((p) => {
    if (p.group !== group) { group = p.group; html += `<div class="group-label">${esc(group)}</div>`; }
    const r = recordFor(p.id), isFavorite = r.favorite || MODALITIES.some((m) => r.images[m.key].some((image) => image.favorite));
    html += `<button class="pathology ${p.id === activeId ? "active" : ""}" data-pathology-id="${esc(p.id)}"><span class="star ${isFavorite ? "on" : ""}">${isFavorite ? "★" : "☆"}</span><span class="name">${esc(p.name)}</span></button>`;
  });
  list.innerHTML = html;
}
async function imageHtml(image) {
  let src = safeUrl(image.url);
  if (image.kind === "blob") { const blob = await idbGet(image.id); if (blob) { src = URL.createObjectURL(blob); objectUrls.push(src); } }
  if (!src) return `<div class="subtle">Image unavailable</div>`;
  return `<img src="${esc(src)}" alt="${esc(image.caption || "Collected image")}">`;
}
async function renderImageCard(image) {
  return `<article class="image-card" data-image-id="${esc(image.id)}"><div class="preview">${await imageHtml(image)}</div><div class="image-info"><input class="caption" value="${esc(image.caption)}" placeholder="Caption / source note"><div class="image-actions"><label class="toggle-row"><input class="image-favorite" type="checkbox" ${image.favorite ? "checked" : ""}> Favorite</label><button class="open-image" type="button">Open</button><button class="remove-image" type="button">Remove</button></div></div></article>`;
}
async function renderDetail() {
  objectUrls.forEach((url) => URL.revokeObjectURL(url)); objectUrls = [];
  const el = document.querySelector("#detail"), p = pathology(activeId);
  if (!p) { el.innerHTML = `<div class="empty">Choose a diagnosis.</div>`; return; }
  const r = recordFor(p.id);
  const columns = await Promise.all(MODALITIES.map(async (m) => {
    const images = r.images[m.key];
    return `<section class="modality" data-modality="${m.key}"><div class="modality-head"><h3>${m.label}</h3><span class="subtle">${images.length} image${images.length === 1 ? "" : "s"}</span></div><div class="search-links"><a href="${searchUrl(p,m)}" target="_blank" rel="noopener">Google images ↗</a><a href="https://radiopaedia.org/search?scope=articles&query=${encodeURIComponent(p.q || p.name)}" target="_blank" rel="noopener">Radiopaedia ↗</a></div><div class="findings"><label>Classic report finding <span class="subtle">(editable)</span></label><textarea class="finding" data-finding-key="${m.key}">${esc(r.findings[m.key])}</textarea></div><div class="dropzone" data-drop-modality="${m.key}"><strong>Paste</strong> a screenshot or drop image files/URLs here</div><div class="image-grid">${(await Promise.all(images.map(renderImageCard))).join("") || `<div class="subtle">No images collected yet.</div>`}</div></section>`;
  }));
  el.innerHTML = `<div class="detail-head"><div><div class="eyebrow">${esc(p.group)}</div><h2>${esc(p.name)}</h2><div class="subtle">Search, curate, and keep multiple images per modality.</div></div><div class="actions"><button id="pathologyFavorite" class="${r.favorite ? "primary" : ""}">${r.favorite ? "★ Favorited" : "☆ Favorite pathology"}</button></div></div><div class="modality-grid">${columns.join("")}</div><div class="notes"><label>Personal note</label><textarea id="personalNotes" placeholder="Optional memory hook, differential, or Anki cue…">${esc(r.notes)}</textarea></div><div class="tip">Shortcuts: <b>/</b> search · <b>Ctrl/Cmd+V</b> paste an image · pathology favorite toggles all images in that pathology.</div>`;
  bindDropzones();
}
function render() { renderList(); renderDetail(); updateStatus(); }
function bindDropzones() {
  document.querySelectorAll(".dropzone").forEach((zone) => {
    zone.addEventListener("click", () => { activeModality = zone.dataset.dropModality; document.querySelector("#imagePicker").click(); });
    zone.addEventListener("dragover", (event) => { event.preventDefault(); activeModality = zone.dataset.dropModality; zone.classList.add("drag"); });
    zone.addEventListener("dragleave", () => zone.classList.remove("drag"));
    zone.addEventListener("drop", async (event) => { event.preventDefault(); zone.classList.remove("drag"); await handleTransfer(event.dataTransfer, zone.dataset.dropModality); });
  });
}
async function handleTransfer(transfer, modality) {
  const files = [...(transfer.files || [])].filter((file) => file.type.startsWith("image/"));
  if (files.length) { for (const file of files) await addImage(modality, file); showToast(`${files.length} image${files.length === 1 ? "" : "s"} added`); return; }
  const url = safeUrl((transfer.getData("text/uri-list") || transfer.getData("text/plain") || "").split("\n")[0].trim());
  if (url) { await addImage(modality, url); showToast("Image URL added"); }
}
async function addImage(modality, payload) {
  const r = recordFor(activeId), id = `image-${Date.now()}-${Math.random().toString(36).slice(2,8)}`;
  const image = { id, kind: typeof payload === "string" ? "url" : "blob", url: typeof payload === "string" ? payload : "", caption:"", favorite:Boolean(r.favorite), createdAt:new Date().toISOString() };
  if (image.kind === "blob") await idbPut(id, payload);
  r.images[modality].push(image); persist(); await renderDetail(); renderList();
}
function togglePathologyFavorite() { const r = recordFor(activeId), next = !r.favorite; r.favorite = next; MODALITIES.forEach((m) => r.images[m.key].forEach((image) => image.favorite = next)); persist(); render(); }
function removeImage(modality, imageId) {
  const r = recordFor(activeId), images = r.images[modality], index = images.findIndex((image) => image.id === imageId); if (index < 0) return;
  const [removed] = images.splice(index,1); if (removed.kind === "blob") idbDelete(removed.id); persist(); renderDetail(); renderList();
}
async function imageAsDataUrl(image) {
  if (image.kind === "url") return image.url;
  const blob = await idbGet(image.id); if (!blob) return "";
  return await new Promise((resolve) => { const reader = new FileReader(); reader.onload = () => resolve(reader.result); reader.onerror = () => resolve(""); reader.readAsDataURL(blob); });
}
async function favoriteExport() {
  const diagnoses = [];
  for (const p of allPathologies()) {
    const r = recordFor(p.id), images = {};
    for (const m of MODALITIES) { images[m.key] = []; for (const image of r.images[m.key]) if (r.favorite || image.favorite) images[m.key].push({...image, data:image.kind === "blob" ? await imageAsDataUrl(image) : undefined}); }
    if (r.favorite || MODALITIES.some((m) => images[m.key].length)) diagnoses.push({id:p.id,name:p.name,group:p.group,favorite:r.favorite,findings:r.findings,notes:r.notes,images});
  }
  return {format:"msk-image-bank",version:1,exportedAt:new Date().toISOString(),diagnoses};
}
async function copyFavorites() {
  const payload = JSON.stringify(await favoriteExport(), null, 2);
  try { await navigator.clipboard.writeText(payload); showToast("Favorites JSON copied"); } catch (_) { const area = document.createElement("textarea"); area.value = payload; document.body.appendChild(area); area.select(); document.execCommand("copy"); area.remove(); showToast("Favorites JSON copied"); }
}
async function downloadFavorites() {
  const blob = new Blob([JSON.stringify(await favoriteExport(), null, 2)], {type:"application/json"}), link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = `msk-image-bank-favorites-${new Date().toISOString().slice(0,10)}.json`; link.click(); URL.revokeObjectURL(link.href); showToast("Favorites exported");
}
async function importBackup(file) {
  const payload = JSON.parse(await file.text()); if (payload.format !== "msk-image-bank" || !Array.isArray(payload.diagnoses)) throw new Error("Not an MSK Image Bank export");
  for (const item of payload.diagnoses) {
    const p = pathology(item.id); if (!p) continue; const r = recordFor(p.id); r.favorite = Boolean(item.favorite); r.notes = item.notes || r.notes; r.findings = {...r.findings,...(item.findings || {})};
    for (const m of MODALITIES) for (const image of item.images?.[m.key] || []) { if (image.data?.startsWith("data:")) { const response = await fetch(image.data), blob = await response.blob(), newId = `image-${Date.now()}-${Math.random().toString(36).slice(2,8)}`; await idbPut(newId,blob); r.images[m.key].push({...image,id:newId,kind:"blob",url:"",favorite:Boolean(image.favorite),data:undefined}); } else if (image.url) r.images[m.key].push({...image,id:`image-${Date.now()}-${Math.random().toString(36).slice(2,8)}`,favorite:Boolean(image.favorite)}); }
  }
  persist(); render(); showToast("Import complete");
}
function addDiagnosis() { const name = prompt("Diagnosis name"); if (!name?.trim()) return; const group = prompt("Group", "My additions") || "My additions"; const id = `${name.toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"")}-${Date.now()}`; state.custom.push({id,name:name.trim(),group,q:name.trim(),findings:{xr:"",ct:"",mri:""}}); activeId = id; persist(); render(); }

document.querySelector("#pathologyList").addEventListener("click", (event) => { const button = event.target.closest("[data-pathology-id]"); if (button) { activeId = button.dataset.pathologyId; render(); } });
document.querySelector("#searchInput").addEventListener("input", renderList);
document.querySelector("#favoritesOnly").addEventListener("change", renderList);
document.querySelector("#addBtn").addEventListener("click", addDiagnosis);
document.querySelector("#openAllBtn").addEventListener("click", () => { const p = pathology(activeId); if (p) MODALITIES.forEach((m) => window.open(searchUrl(p,m),"_blank")); });
document.querySelector("#copyBtn").addEventListener("click", copyFavorites);
document.querySelector("#exportBtn").addEventListener("click", downloadFavorites);
document.querySelector("#importBtn").addEventListener("click", () => document.querySelector("#importInput").click());
document.querySelector("#importInput").addEventListener("change", async (event) => { try { if (event.target.files[0]) await importBackup(event.target.files[0]); } catch (error) { showToast(`Import failed: ${error.message}`); } event.target.value = ""; });
document.querySelector("#imagePicker").addEventListener("change", async (event) => { for (const file of event.target.files) await addImage(activeModality, file); if (event.target.files.length) showToast(`${event.target.files.length} image${event.target.files.length === 1 ? "" : "s"} added`); event.target.value = ""; });
document.querySelector("#detail").addEventListener("click", (event) => {
  if (event.target.id === "pathologyFavorite") return togglePathologyFavorite();
  const card = event.target.closest(".image-card"), modality = event.target.closest("[data-modality]")?.dataset.modality; if (!card || !modality) return;
  const image = recordFor(activeId).images[modality].find((item) => item.id === card.dataset.imageId); if (!image) return;
  if (event.target.classList.contains("remove-image")) return removeImage(modality,image.id);
  if (event.target.classList.contains("open-image")) { const url = image.kind === "url" ? image.url : card.querySelector("img")?.src; if (url) window.open(url,"_blank"); }
});
document.querySelector("#detail").addEventListener("input", (event) => {
  const r = recordFor(activeId);
  if (event.target.id === "personalNotes") { r.notes = event.target.value; persist(); return; }
  if (event.target.classList.contains("finding")) { r.findings[event.target.dataset.findingKey] = event.target.value; persist(); return; }
  if (event.target.classList.contains("caption")) { const card = event.target.closest(".image-card"), modality = event.target.closest("[data-modality]")?.dataset.modality, image = r.images[modality]?.find((item) => item.id === card?.dataset.imageId); if (image) { image.caption = event.target.value; persist(); } }
});
document.querySelector("#detail").addEventListener("change", (event) => { if (!event.target.classList.contains("image-favorite")) return; const card = event.target.closest(".image-card"), modality = event.target.closest("[data-modality]")?.dataset.modality, image = recordFor(activeId).images[modality]?.find((item) => item.id === card?.dataset.imageId); if (image) { image.favorite = event.target.checked; persist(); renderList(); } });
document.addEventListener("paste", async (event) => {
  if (!activeId) return; const items = [...(event.clipboardData?.items || [])], imageItem = items.find((item) => item.type.startsWith("image/"));
  if (imageItem) { event.preventDefault(); await addImage(activeModality,imageItem.getAsFile()); showToast(`Screenshot pasted to ${activeModality.toUpperCase()}`); return; }
  const text = safeUrl(event.clipboardData?.getData("text/plain") || ""); if (text && document.activeElement.tagName !== "INPUT" && document.activeElement.tagName !== "TEXTAREA") { await addImage(activeModality,text); showToast("Image URL pasted"); }
});
document.addEventListener("keydown", (event) => { if (event.key === "/" && !["INPUT","TEXTAREA"].includes(document.activeElement.tagName)) { event.preventDefault(); document.querySelector("#searchInput").focus(); } });
render();
