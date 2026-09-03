const MODALITIES = [{key:"xr",label:"Radiograph"},{key:"ct",label:"CT"},{key:"mri",label:"MRI"}];
const select = document.querySelector("#pathologySelect"), track = document.querySelector("#track"), stage = document.querySelector("#stage"), loading = document.querySelector("#loading"), loadingText = document.querySelector("#loadingText"), counter = document.querySelector("#counter");
let pathologies = [], slides = [], current = 0, requestToken = 0, touchY = null, lastTouchY = null, touchTicks = 0;

function esc(value) { return String(value ?? "").replace(/[&<>"']/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[char])); }
function fallbackBank() {
  const seed = typeof PATHOLOGIES !== "undefined" ? PATHOLOGIES : [];
  return {pathologies: seed.map((p) => ({...p, images:{xr:[],ct:[],mri:[]},notes:"",favorite:false}))};
}
async function loadBank() {
  try { const response = await fetch("data.json", {cache:"no-store"}); if (!response.ok) throw new Error("data unavailable"); return await response.json(); }
  catch (_) { return fallbackBank(); }
}
function imageEntries(pathology) {
  return MODALITIES.flatMap((modality) => (pathology.images?.[modality.key] || []).map((image) => ({...image, modality:modality.label})));
}
function preload(entry) {
  return new Promise((resolve) => { const image = new Image(); image.decoding = "async"; image.onload = () => resolve({...entry,ready:true}); image.onerror = () => resolve({...entry,ready:false}); image.src = entry.src || entry.url || ""; });
}
function setLoading(visible, text="Loading images…") { loading.hidden = !visible; loadingText.textContent = text; }
function renderSlides() {
  if (!slides.length) { track.style.transform = "none"; track.innerHTML = `<div class="empty">No published images for this pathology yet.</div>`; counter.textContent = "0 images"; return; }
  track.innerHTML = slides.map((image, index) => `<section class="slide"><img src="${esc(image.src || image.url)}" alt="${esc(image.caption || "Collected image")}"><div class="label"><span>${esc(image.modality)}${image.caption ? ` · ${esc(image.caption)}` : ""}</span><span>${index + 1} / ${slides.length}</span></div></section>`).join("");
  current = 0; track.style.transform = "translateY(0)"; counter.textContent = `1 / ${slides.length}`;
}
function move(step) {
  if (!slides.length) return;
  current = Math.max(0, Math.min(slides.length - 1, current + step));
  track.style.transform = `translateY(-${current * 100}%)`; counter.textContent = `${current + 1} / ${slides.length}`;
}
async function choosePathology(id) {
  const token = ++requestToken, pathology = pathologies.find((item) => item.id === id);
  if (!pathology) return;
  const entries = imageEntries(pathology); slides = []; current = 0; track.innerHTML = ""; setLoading(true, entries.length ? `Loading 0 / ${entries.length} images…` : "Loading…");
  let completed = 0;
  const results = await Promise.all(entries.map((entry) => preload(entry).then((result) => { completed += 1; if (token === requestToken) loadingText.textContent = `Loading ${completed} / ${entries.length} images…`; return result; })));
  if (token !== requestToken) return;
  slides = results.filter((result) => result.ready); renderSlides(); setLoading(false);
}
function populateSelect() {
  select.innerHTML = pathologies.map((pathology) => `<option value="${esc(pathology.id)}">${esc(pathology.name)}</option>`).join("");
  if (pathologies.length) choosePathology(pathologies[0].id);
}
stage.addEventListener("touchstart", (event) => { if (!event.touches.length) return; touchY = lastTouchY = event.touches[0].clientY; touchTicks = 0; }, {passive:true});
stage.addEventListener("touchmove", (event) => { if (touchY === null || !event.touches.length) return; event.preventDefault(); const y = event.touches[0].clientY, delta = y - lastTouchY; if (Math.abs(delta) >= 22) { move(delta < 0 ? 1 : -1); lastTouchY = y; touchTicks += 1; } }, {passive:false});
stage.addEventListener("touchend", (event) => { if (touchY === null) return; const y = event.changedTouches[0]?.clientY ?? touchY; if (!touchTicks && Math.abs(y - touchY) >= 12) move(y < touchY ? 1 : -1); touchY = lastTouchY = null; });
stage.addEventListener("wheel", (event) => { event.preventDefault(); if (Math.abs(event.deltaY) >= 4) move(event.deltaY > 0 ? 1 : -1); }, {passive:false});
select.addEventListener("change", () => choosePathology(select.value));
window.addEventListener("keydown", (event) => { if (event.key === "ArrowDown" || event.key === "ArrowRight") move(1); if (event.key === "ArrowUp" || event.key === "ArrowLeft") move(-1); });
loadBank().then((bank) => { pathologies = bank.pathologies || []; populateSelect(); }).catch((error) => { track.innerHTML = `<div class="error">Unable to load the image bank.<br>${esc(error.message)}</div>`; });
