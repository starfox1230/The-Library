const T = SiteTimer;
const requested = new URLSearchParams(location.search).get("site");
const site = T.SITES[requested] ? requested : "facebook";
document.getElementById("settings").addEventListener("click", () => chrome.runtime.openOptionsPage());
const retry = document.getElementById("retry");
retry.href = T.SITES[site].home;
async function refresh() {
  try {
    const result = await chrome.runtime.sendMessage({ type: "status" });
    if (!result?.ok) throw new Error();
    document.getElementById("label").textContent = T.SITES[site].name + " · today";
    document.getElementById("total").textContent = T.format(result.sites[site].todayMs);
    document.getElementById("reason").textContent = result.sites[site].blocked || "Your limit has cleared. You can open " + T.SITES[site].name + " again.";
    retry.textContent = result.sites[site].blocked ? "Check again" : "Open " + T.SITES[site].name;
  } catch { document.getElementById("reason").textContent = "Open extension settings to check your limits."; }
}
refresh();
setInterval(refresh, 1000);
