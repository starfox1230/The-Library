const status = document.getElementById("status");

chrome.runtime.sendMessage({ type: "sct-popup-status" }, (response) => {
  if (response?.ok) {
    status.className = "good";
    status.textContent = "Connected to Screen Capture Transcriber.";
  } else {
    status.className = "bad";
    status.textContent = "Recorder not connected. Open or restart the desktop app.";
  }
});
