const home = "C:\\Users\\sterl\\Documents\\Chrome Extensions";
const status = document.getElementById("status");
async function copy(value, button) {
  try {
    await navigator.clipboard.writeText(value);
    button.textContent = "Copied";
    setTimeout(() => { button.textContent = "Copy path"; }, 1800);
  } catch { status.textContent = "Select and copy this path: " + value; }
}
document.getElementById("copy-home").addEventListener("click", event => copy(home, event.currentTarget));
fetch("registry.json").then(response => {
  if (!response.ok) throw new Error();
  return response.json();
}).then(extensions => {
  document.getElementById("count").textContent = extensions.length + " EXTENSIONS";
  for (const item of extensions) {
    const card = document.createElement("article");
    card.className = "card" + (item.slug === "website-timer" ? " featured" : "");
    const badge = document.createElement("div");
    badge.className = "badge";
    badge.textContent = item.slug === "website-timer" ? "NEW · YOUR TIME, VISIBLE" : item.slug === "screen-capture-transcriber" ? "READY TO LOAD" : "EXISTING CUSTOM EXTENSION";
    const title = document.createElement("h3");
    title.textContent = item.name;
    const description = document.createElement("p");
    description.textContent = item.description;
    const path = document.createElement("code");
    path.textContent = home + "\\" + item.folder;
    const actions = document.createElement("div");
    actions.className = "card-actions";
    const button = document.createElement("button");
    button.textContent = "Copy path";
    button.addEventListener("click", () => copy(path.textContent, button));
    const source = document.createElement("a");
    source.href = "https://github.com/starfox1230/The-Library/tree/main/" + item.source;
    source.textContent = "View source ↗";
    actions.append(button, source);
    card.append(badge, title, description, path, actions);
    document.getElementById("extensions").append(card);
  }
}).catch(() => { status.textContent = "Could not load the extension catalog. Open the source link below for the folder list."; });
