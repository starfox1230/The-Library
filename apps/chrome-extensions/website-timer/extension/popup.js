const T = SiteTimer;
const form = document.getElementById("settings");
const status = document.getElementById("status");
let dirty = false, built = false, polling = false;
function render(result) {
  document.getElementById("day").textContent = "Today · " + result.day;
  if (!built) {
    document.getElementById("sites").innerHTML = Object.entries(T.SITES).map(([site, info]) => `
      <section class="site" data-site="${site}">
        <div class="site-head"><div><h2>${info.name}</h2><small>${info.domain}</small></div><span class="total" aria-label="${info.name} time today">00:00</span></div>
        <div class="policies">
          <div class="policy"><label><input type="checkbox" name="${site}-dailyEnabled"> Daily time limit</label><span class="minutes"><input type="number" name="${site}-dailyMinutes" min="1" max="1440" required aria-label="${info.name} daily limit in minutes"> min</span></div>
          <div class="policy"><label><input type="checkbox" name="${site}-cutoffEnabled"> Block after</label><input type="time" name="${site}-cutoff" required aria-label="${info.name} daily cutoff time"></div>
          <p class="block-state"></p>
        </div>
      </section>`).join("");
    built = true;
  }
  for (const site of Object.keys(T.SITES)) {
    const card = document.querySelector('[data-site="' + site + '"]');
    card.querySelector(".total").textContent = T.format(result.sites[site].todayMs);
    card.querySelector(".block-state").textContent = result.sites[site].blocked || "Available · " + ((result.settings[site].dailyEnabled || result.settings[site].cutoffEnabled) ? "your limits are on" : "timer only");
    if (!dirty) for (const [key, value] of Object.entries(result.settings[site])) {
      const input = form.elements[site + "-" + key];
      if (input.type === "checkbox") input.checked = value;
      else input.value = value;
    }
  }
}
form.addEventListener("input", () => { dirty = true; status.textContent = "Unsaved changes"; });
form.addEventListener("submit", async event => {
  event.preventDefault();
  const button = form.querySelector("button");
  button.disabled = true;
  try {
    const settings = Object.fromEntries(Object.keys(T.SITES).map(site => [site, {
      dailyEnabled: form.elements[site + "-dailyEnabled"].checked,
      dailyMinutes: Number(form.elements[site + "-dailyMinutes"].value),
      cutoffEnabled: form.elements[site + "-cutoffEnabled"].checked,
      cutoff: form.elements[site + "-cutoff"].value
    }]));
    const result = await chrome.runtime.sendMessage({ type: "saveSettings", settings });
    if (!result?.ok) throw new Error(result?.error || "Could not save limits.");
    dirty = false;
    render(result);
    status.textContent = "Saved. Limits apply immediately.";
  } catch (error) { status.textContent = error.message; }
  finally { button.disabled = false; }
});
async function refresh() {
  if (polling) return;
  polling = true;
  try {
    const result = await chrome.runtime.sendMessage({ type: "status" });
    if (!result?.ok) throw new Error("Could not connect to the timer.");
    render(result);
  } catch (error) { status.textContent = error.message; }
  finally { polling = false; }
}
refresh();
setInterval(refresh, 1000);
